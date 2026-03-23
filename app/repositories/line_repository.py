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