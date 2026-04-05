from sqlalchemy import text
import json

from app.services.line_api import get_chat_identity, get_profile_data, get_group_summary


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
        INSERT INTO line_event_logs (
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
        FROM line_chats
        WHERE chat_type = :chat_type
        AND chat_id = :chat_id
    """)
    row = session.execute(select_sql, {
        "chat_type": chat_type,
        "chat_id": chat_id
    }).mappings().first()

    if row:
        update_fields = ["last_seen_at = CURRENT_TIMESTAMP"]
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
                update_fields.append("bot_joined_at = COALESCE(bot_joined_at, CURRENT_TIMESTAMP)")
                update_fields.append("bot_left_at = NULL")
            elif bot_status == "left":
                update_fields.append("bot_left_at = CURRENT_TIMESTAMP")

        update_sql = text(f"""
            UPDATE line_chats
            SET {", ".join(update_fields)}
            WHERE id = :id
        """)
        session.execute(update_sql, params)
        return row["id"]

    insert_sql = text("""
        INSERT INTO line_chats (
            chat_type,
            chat_id,
            group_name,
            bot_status,
            bot_joined_at,
            bot_left_at,
            last_seen_at
        )
        VALUES (
            :chat_type,
            :chat_id,
            :group_name,
            :bot_status,
            :bot_joined_at,
            :bot_left_at,
            CURRENT_TIMESTAMP
        )
        RETURNING id
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
            UPDATE line_chats
            SET bot_joined_at = COALESCE(bot_joined_at, CURRENT_TIMESTAMP)
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
        FROM line_users
        WHERE user_id = :user_id
    """)
    row = session.execute(select_sql, {"user_id": user_id}).mappings().first()

    if row:
        update_fields = ["last_seen_at = CURRENT_TIMESTAMP"]
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
            UPDATE line_users
            SET {", ".join(update_fields)}
            WHERE id = :id
        """)
        session.execute(update_sql, params)
        return row["id"]

    insert_sql = text("""
        INSERT INTO line_users (
            user_id,
            display_name,
            picture_url,
            status_message,
            language,
            is_friend,
            status,
            last_seen_at
        )
        VALUES (
            :user_id,
            :display_name,
            :picture_url,
            :status_message,
            :language,
            :is_friend,
            :status,
            CURRENT_TIMESTAMP
        )
        RETURNING id
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
        FROM line_chat_memberships
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
                UPDATE line_chat_memberships
                SET status = 'active',
                    joined_at = COALESCE(joined_at, CURRENT_TIMESTAMP),
                    left_at = NULL,
                    last_seen_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """)
        else:
            update_sql = text("""
                UPDATE line_chat_memberships
                SET status = 'left',
                    left_at = CURRENT_TIMESTAMP,
                    last_seen_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """)

        session.execute(update_sql, {"id": row["id"]})
        return

    insert_sql = text("""
        INSERT INTO line_chat_memberships (
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
            CURRENT_TIMESTAMP
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
            UPDATE line_chat_memberships
            SET joined_at = COALESCE(joined_at, CURRENT_TIMESTAMP)
            WHERE chat_pk = :chat_pk
            AND line_user_pk = :line_user_pk
        """), {
            "chat_pk": chat_pk,
            "line_user_pk": line_user_pk
        })
    else:
        session.execute(text("""
            UPDATE line_chat_memberships
            SET left_at = CURRENT_TIMESTAMP
            WHERE chat_pk = :chat_pk
            AND line_user_pk = :line_user_pk
        """), {
            "chat_pk": chat_pk,
            "line_user_pk": line_user_pk
        })


def upsert_internal_user(session, line_user_id):
    if not line_user_id:
        return None

    row = session.execute(text("""
        SELECT id, is_active
        FROM users
        WHERE line_user_id = :line_user_id
    """), {"line_user_id": line_user_id}).mappings().first()

    if row:
        session.execute(text("""
            UPDATE users
            SET is_active = 1,
                failed_login_count = 0
            WHERE id = :id
        """), {"id": row["id"]})
        return row["id"]

    return session.execute(text("""
        INSERT INTO users (
            line_user_id,
            is_active,
            created_at,
            updated_at
        )
        VALUES (
            :line_user_id,
            1,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        RETURNING id
    """), {"line_user_id": line_user_id}).scalar()


def deactivate_internal_user(session, line_user_id):
    if not line_user_id:
        return

    session.execute(text("""
        UPDATE users
        SET is_active = 0
        WHERE line_user_id = :line_user_id
    """), {"line_user_id": line_user_id})


def is_event_processed(session, webhook_event_id):
    if not webhook_event_id:
        return False

    row = session.execute(text("""
        SELECT 1
        FROM line_processed_events
        WHERE webhook_event_id = :webhook_event_id
    """), {"webhook_event_id": webhook_event_id}).first()

    return row is not None


def mark_event_processed(session, webhook_event_id, event_type):
    if not webhook_event_id:
        return

    session.execute(text("""
        INSERT INTO line_processed_events (
            webhook_event_id,
            event_type
        )
        VALUES (
            :webhook_event_id,
            :event_type
        )
    """), {
        "webhook_event_id": webhook_event_id,
        "event_type": event_type
    })