from flask import Blueprint, request, jsonify

from app.db.db_connection import db
from app.services.line_signature import verify_signature
from app.repositories.line_repository import (
    log_event,
    upsert_line_chat,
    upsert_line_user,
    upsert_membership,
    upsert_internal_user,
    deactivate_internal_user,
    is_event_processed,
    mark_event_processed
)
from app.services.line_api import get_profile_data

webhook_bp = Blueprint("webhook", __name__)


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
            webhook_event_id = event.get("webhookEventId")
            is_redelivery = event.get("deliveryContext", {}).get("isRedelivery", False)

            print({
                "event_type": event.get("type"),
                "timestamp": event.get("timestamp"),
                "is_redelivery": is_redelivery,
                "webhook_event_id": webhook_event_id,
                "source_type": source.get("type"),
                "source_user_id": source.get("userId"),
                "group_id": source.get("groupId"),
                "room_id": source.get("roomId"),
            })

            if webhook_event_id and is_event_processed(session, webhook_event_id):
                print(f"⏭️ Skip duplicated event: {webhook_event_id}")
                continue

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
                    upsert_internal_user(session, joined_user_id)

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
                        status="left"
                    )
                    upsert_membership(
                        session=session,
                        chat_pk=chat_pk,
                        line_user_pk=line_user_pk,
                        active=False
                    )
                    deactivate_internal_user(session, left_user_id)

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
                upsert_internal_user(session, uid)

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
                deactivate_internal_user(session, uid)

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
                    upsert_internal_user(session, uid)

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
                    upsert_internal_user(session, uid)

                print(f"📨 Postback from user_id={uid}")

            else:
                print(f"ℹ️ Unhandled event type: {event_type}")

            if webhook_event_id:
                mark_event_processed(session, webhook_event_id, event_type)

        session.commit()
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        session.rollback()
        print(f"❌ Webhook Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        session.close()