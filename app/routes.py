from flask import Blueprint, request, jsonify
from sqlalchemy import text
import hmac
import hashlib
import base64
import requests
import json

from app.config import Config
from app.db.db_connection import db

webhook_bp = Blueprint("webhook", __name__)


def verify_signature(body, signature):
    digest = hmac.new(
        Config.LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature or "")


def get_line_headers():
    return {
        "Authorization": f"Bearer {Config.LINE_ACCESS_TOKEN}"
    }


def get_chat_identity(source):
    stype = source.get("type")

    if stype == "group":
        return "group", source.get("groupId")
    elif stype == "room":
        return "room", source.get("roomId")
    elif stype == "user":
        return "user", source.get("userId")

    return None, None


def get_profile_data(source, user_id):
    if not user_id:
        return {
            "display_name": None,
            "picture_url": None,
            "status_message": None,
            "language": None
        }

    stype = source.get("type")

    if stype == "group":
        url = f"https://api.line.me/v2/bot/group/{source.get('groupId')}/member/{user_id}"
    elif stype == "room":
        url = f"https://api.line.me/v2/bot/room/{source.get('roomId')}/member/{user_id}"
    else:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"

    try:
        res = requests.get(url, headers=get_line_headers(), timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "display_name": data.get("displayName"),
                "picture_url": data.get("pictureUrl"),
                "status_message": data.get("statusMessage"),
                "language": data.get("language")
            }
    except Exception as e:
        print(f"❌ get_profile_data error: {str(e)}")

    return {
        "display_name": None,
        "picture_url": None,
        "status_message": None,
        "language": None
    }


def get_group_summary(group_id):
    if not group_id:
        return {}

    url = f"https://api.line.me/v2/bot/group/{group_id}/summary"

    try:
        res = requests.get(url, headers=get_line_headers(), timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"❌ get_group_summary error: {str(e)}")

    return {}


def log_event(session, event):
    source = event.get("source", {})
    chat_type, chat_id = get_chat_identity(source)

    line_user_id = source.get("userId")

    if not line_user_id:
        members = event.get("joined", {}).get("members", [])
        if not members:
            members = event.get("left", {}).get("members", [])
        if members:
            line_user_id = members[0].get("userId")

    sql = text("""
        INSERT INTO dbo.line_event_logs (
            event_type,
            chat_type,
            chat_id,
            line_user_id,
            event_timestamp,
            raw_json
        )
        VALUES (
            :event_type,
            :chat_type,
            :chat_id,
            :line_user_id,
            :event_timestamp,
            :raw_json
        )
    """)

    session.execute(sql, {
        "event_type": event.get("type"),
        "chat_type": chat_type,
        "chat_id": chat_id,
        "line_user_id": line_user_id,
        "event_timestamp": event.get("timestamp"),
        "raw_json": json.dumps(event, ensure_ascii=False)
    })


def upsert_line_chat(session, source, bot_status=None):
    chat_type, chat_id = get_chat_identity(source)

    if not chat_type or not chat_id:
        return None

    group_name = None
    if chat_type == "group":
        summary = get_group_summary(chat_id)
        group_name = summary.get("groupName")

    select_sql = text("""
        SELECT id, chat_type, chat_id, group_name, bot_status
        FROM dbo.line_chats
        WHERE chat_type = :chat_type
        AND chat_id = :chat_id
    """)
    row = session.execute(select_sql, {
        "chat_type": chat_type,
        "chat_id": chat_id
    }).mappings().first()

    if row:
        update_fields = ["last_seen_at = SYSUTCDATETIME()"]
        params = {
            "id": row["id"]
        }

        if group_name:
            update_fields.append("group_name = :group_name")
            params["group_name"] = group_name

        if bot_status:
            update_fields.append("bot_status = :bot_status")
            params["bot_status"] = bot_status

            if bot_status == "active":
                update_fields.append("bot_joined_at = ISNULL(bot_joined_at, SYSUTCDATETIME())")
                update_fields.append("bot_left_at = NULL")
            elif bot_status == "left":
                update_fields.append("bot_left_at = SYSUTCDATETIME()")

        update_sql = text(f"""
            UPDATE dbo.line_chats
            SET {", ".join(update_fields)}
            WHERE id = :id
        """)
        session.execute(update_sql, params)
        return row["id"]

    insert_sql = text("""
        INSERT INTO dbo.line_chats (
            chat_type,
            chat_id,
            group_name,
            bot_status,
            bot_joined_at,
            bot_left_at,
            last_seen_at
        )
        OUTPUT INSERTED.id
        VALUES (
            :chat_type,
            :chat_id,
            :group_name,
            :bot_status,
            :bot_joined_at,
            :bot_left_at,
            SYSUTCDATETIME()
        )
    """)

    if not bot_status:
        bot_status = "active"

    chat_id_inserted = session.execute(insert_sql, {
        "chat_type": chat_type,
        "chat_id": chat_id,
        "group_name": group_name,
        "bot_status": bot_status,
        "bot_joined_at": None if bot_status != "active" else None,
        "bot_left_at": None
    }).scalar()

    if bot_status == "active":
        session.execute(text("""
            UPDATE dbo.line_chats
            SET bot_joined_at = ISNULL(bot_joined_at, SYSUTCDATETIME())
            WHERE id = :id
        """), {"id": chat_id_inserted})

    return chat_id_inserted


def upsert_line_user(session, user_id, source=None, is_friend=None, status=None):
    if not user_id:
        return None

    profile = {
        "display_name": None,
        "picture_url": None,
        "status_message": None,
        "language": None
    }

    if source:
        profile = get_profile_data(source, user_id)

    select_sql = text("""
        SELECT id, user_id, display_name, is_friend, status
        FROM dbo.line_users
        WHERE user_id = :user_id
    """)
    row = session.execute(select_sql, {"user_id": user_id}).mappings().first()

    if row:
        update_fields = ["last_seen_at = SYSUTCDATETIME()"]
        params = {"id": row["id"]}

        if profile.get("display_name"):
            update_fields.append("display_name = :display_name")
            params["display_name"] = profile["display_name"]

        if profile.get("picture_url"):
            update_fields.append("picture_url = :picture_url")
            params["picture_url"] = profile["picture_url"]

        if profile.get("status_message"):
            update_fields.append("status_message = :status_message")
            params["status_message"] = profile["status_message"]

        if profile.get("language"):
            update_fields.append("language = :language")
            params["language"] = profile["language"]

        if is_friend is not None:
            update_fields.append("is_friend = :is_friend")
            params["is_friend"] = 1 if is_friend else 0

        if status:
            update_fields.append("status = :status")
            params["status"] = status

        update_sql = text(f"""
            UPDATE dbo.line_users
            SET {", ".join(update_fields)}
            WHERE id = :id
        """)
        session.execute(update_sql, params)
        return row["id"]

    insert_sql = text("""
        INSERT INTO dbo.line_users (
            user_id,
            display_name,
            picture_url,
            status_message,
            language,
            is_friend,
            status,
            last_seen_at
        )
        OUTPUT INSERTED.id
        VALUES (
            :user_id,
            :display_name,
            :picture_url,
            :status_message,
            :language,
            :is_friend,
            :status,
            SYSUTCDATETIME()
        )
    """)

    line_user_id = session.execute(insert_sql, {
        "user_id": user_id,
        "display_name": profile.get("display_name"),
        "picture_url": profile.get("picture_url"),
        "status_message": profile.get("status_message"),
        "language": profile.get("language"),
        "is_friend": 1 if is_friend else 0,
        "status": status or "active"
    }).scalar()

    return line_user_id


def upsert_membership(session, chat_pk, line_user_pk, active=True):
    if not chat_pk or not line_user_pk:
        return

    select_sql = text("""
        SELECT id, status, joined_at, left_at
        FROM dbo.line_chat_memberships
        WHERE chat_pk = :chat_pk
        AND line_user_pk = :line_user_pk
    """)
    row = session.execute(select_sql, {
        "chat_pk": chat_pk,
        "line_user_pk": line_user_pk
    }).mappings().first()

    if row:
        if active:
            update_sql = text("""
                UPDATE dbo.line_chat_memberships
                SET status = 'active',
                    joined_at = ISNULL(joined_at, SYSUTCDATETIME()),
                    left_at = NULL,
                    last_seen_at = SYSUTCDATETIME()
                WHERE id = :id
            """)
        else:
            update_sql = text("""
                UPDATE dbo.line_chat_memberships
                SET status = 'left',
                    left_at = SYSUTCDATETIME(),
                    last_seen_at = SYSUTCDATETIME()
                WHERE id = :id
            """)

        session.execute(update_sql, {"id": row["id"]})
        return

    insert_sql = text("""
        INSERT INTO dbo.line_chat_memberships (
            chat_pk,
            line_user_pk,
            status,
            joined_at,
            left_at,
            last_seen_at
        )
        VALUES (
            :chat_pk,
            :line_user_pk,
            :status,
            :joined_at,
            :left_at,
            SYSUTCDATETIME()
        )
    """)

    session.execute(insert_sql, {
        "chat_pk": chat_pk,
        "line_user_pk": line_user_pk,
        "status": "active" if active else "left",
        "joined_at": None if not active else None,
        "left_at": None
    })

    if active:
        session.execute(text("""
            UPDATE dbo.line_chat_memberships
            SET joined_at = ISNULL(joined_at, SYSUTCDATETIME())
            WHERE chat_pk = :chat_pk
            AND line_user_pk = :line_user_pk
        """), {
            "chat_pk": chat_pk,
            "line_user_pk": line_user_pk
        })
    else:
        session.execute(text("""
            UPDATE dbo.line_chat_memberships
            SET left_at = SYSUTCDATETIME()
            WHERE chat_pk = :chat_pk
            AND line_user_pk = :line_user_pk
        """), {
            "chat_pk": chat_pk,
            "line_user_pk": line_user_pk
        })


@webhook_bp.route("/webhook", methods=["POST"])
def line_webhook():
    body = request.get_data()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, signature):
        return jsonify({"status": "error", "message": "Unauthorized"}), 400

    data = request.get_json(silent=True) or {}
    events = data.get("events", [])

    session = db.get_session()

    try:
        for event in events:
            source = event.get("source", {})
            event_type = event.get("type")
            uid = source.get("userId")

            log_event(session, event)

            # 1) Bot joined group/room
            if event_type == "join":
                chat_pk = upsert_line_chat(session, source, bot_status="active")
                print(f"🤝 Bot joined chat, chat_pk={chat_pk}")

            # 2) Bot left group/room
            elif event_type == "leave":
                chat_pk = upsert_line_chat(session, source, bot_status="left")
                print(f"🏠 Bot left chat, chat_pk={chat_pk}")

            # 3) Member joined
            elif event_type == "memberJoined":
                chat_pk = upsert_line_chat(session, source)

                for m in event.get("joined", {}).get("members", []):
                    joined_user_id = m.get("userId")
                    line_user_pk = upsert_line_user(
                        session=session,
                        user_id=joined_user_id,
                        source=source,
                        status="active"
                    )
                    upsert_membership(
                        session=session,
                        chat_pk=chat_pk,
                        line_user_pk=line_user_pk,
                        active=True
                    )
                    print(f"🆕 Member joined: user_id={joined_user_id}, chat_pk={chat_pk}")

            # 4) Member left
            elif event_type == "memberLeft":
                chat_pk = upsert_line_chat(session, source)

                for m in event.get("left", {}).get("members", []):
                    left_user_id = m.get("userId")
                    line_user_pk = upsert_line_user(
                        session=session,
                        user_id=left_user_id,
                        source=None,
                        status="active"
                    )
                    upsert_membership(
                        session=session,
                        chat_pk=chat_pk,
                        line_user_pk=line_user_pk,
                        active=False
                    )
                    print(f"❌ Member left: user_id={left_user_id}, chat_pk={chat_pk}")

            # 5) Follow (1:1 add friend)
            elif event_type == "follow":
                chat_pk = upsert_line_chat(session, source, bot_status="active")
                line_user_pk = upsert_line_user(
                    session=session,
                    user_id=uid,
                    source=source,
                    is_friend=True,
                    status="active"
                )
                upsert_membership(
                    session=session,
                    chat_pk=chat_pk,
                    line_user_pk=line_user_pk,
                    active=True
                )
                print(f"➕ Follow: user_id={uid}")

            # 6) Unfollow (1:1 block OA)
            elif event_type == "unfollow":
                line_user_pk = upsert_line_user(
                    session=session,
                    user_id=uid,
                    source=None,
                    is_friend=False,
                    status="blocked"
                )
                print(f"🚫 Unfollow: user_id={uid}, line_user_pk={line_user_pk}")

            # 7) Message
            elif event_type == "message":
                chat_pk = upsert_line_chat(session, source)

                if uid:
                    line_user_pk = upsert_line_user(
                        session=session,
                        user_id=uid,
                        source=source,
                        status="active"
                    )
                    upsert_membership(
                        session=session,
                        chat_pk=chat_pk,
                        line_user_pk=line_user_pk,
                        active=True
                    )

                message = event.get("message", {})
                if message.get("type") == "text":
                    text_message = message.get("text", "")
                    if text_message.startswith("รับทราบ"):
                        name = get_profile_data(source, uid).get("display_name") if uid else "Unknown"
                        print("\n" + "=" * 45)
                        print(f"👷 งานถูกรับแล้วโดย: {name}")
                        print(f"💬 ข้อความ: {text_message}")
                        print("=" * 45 + "\n")

            # 8) Postback
            elif event_type == "postback":
                chat_pk = upsert_line_chat(session, source)

                if uid:
                    line_user_pk = upsert_line_user(
                        session=session,
                        user_id=uid,
                        source=source,
                        status="active"
                    )
                    upsert_membership(
                        session=session,
                        chat_pk=chat_pk,
                        line_user_pk=line_user_pk,
                        active=True
                    )
                print(f"📨 Postback from user_id={uid}")

            else:
                print(f"ℹ️ Unhandled event type: {event_type}")

        session.commit()
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        session.rollback()
        print(f"❌ Webhook Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        session.close()