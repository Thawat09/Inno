import re
import email
import imaplib
from datetime import datetime, timedelta
from app.config import Config
from app.utils.text_utils import decode_mime_words
from app.utils.extract_utils import extract_email_body
from app.parsers.ticket_parser import extract_ticket_info, identify_task_and_parent
from app.routing.team_router import (
    apply_cross_task_inference,
    detect_assigned_team_by_to,
)
from app.builders.dataset_builder import (
    build_audit_raw_record,
    build_master_db_record,
    build_text_input,
)
from app.services.cloud_subteam_classifier import (
    decide_cloud_subteam_runtime,
)
from app.repositories.email_ticket_repository import (
    task_already_recorded,
    save_master_and_audit_record,
)


def should_send_task(task_id, processed_tasks):
    if not task_id:
        return False

    if task_already_recorded(task_id):
        return False

    if task_id in processed_tasks:
        return False

    return True


# =========================================================
# 4) MAIN FETCH
# =========================================================
def fetch_and_group_tasks(save_to_db=True):
    processed_tasks = set()
    all_tasks_list = []
    parent_groups = {}
    mail = None

    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=Config.IMAP_TIMEOUT)
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        select_status, _ = mail.select(Config.MAILBOX_FOLDER)

        if select_status != "OK":
            print(f"❌ ไม่สามารถเปิด mailbox folder: {Config.MAILBOX_FOLDER}")
            return []

        since_date = (datetime.now() - timedelta(days=Config.DAYS_BACK)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since_date}")')

        if status != "OK":
            print("❌ ไม่สามารถค้นหาอีเมลได้")
            return []

        ids = messages[0].split()

        if Config.MAX_EMAILS is not None:
            ids = ids[-Config.MAX_EMAILS:]

        if not ids:
            return []

        for m_id in reversed(ids):
            try:
                status, msg_data = mail.fetch(m_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                from_address = decode_mime_words(msg.get("From", ""))
                to_address = decode_mime_words(msg.get("To", "")).lower()
                subject = decode_mime_words(msg.get("Subject", ""))

                if Config.TARGET_SENDER.lower() not in from_address.lower():
                    continue

                clean_body = extract_email_body(msg)
                info = extract_ticket_info(clean_body, subject)
                task_id, parent_id = identify_task_and_parent(info)

                if not should_send_task(task_id, processed_tasks):
                    continue

                assigned_team_key = detect_assigned_team_by_to(to_address)

                if not assigned_team_key:
                    continue

                ml_confidence = None
                decision_mode = None

                if assigned_team_key == "iNET Network Team":
                    main_team = "iNET Network Team"
                    sub_team = None
                    label_source = "to_address"
                    decision_mode = "to_address_routing"

                elif assigned_team_key == "iNET Operation Team":
                    main_team = "iNET Operation Team"
                    sub_team = None
                    label_source = "to_address"
                    decision_mode = "to_address_routing"

                elif assigned_team_key == "iNET Cloud Support Team":
                    main_team = "iNET Cloud Support Team"

                    sub_team, label_source, decision_info = decide_cloud_subteam_runtime(
                        info,
                        clean_body,
                        subject,
                        to_address,
                        task_id=task_id
                    )

                    ml_confidence = decision_info.get("ml_confidence")
                    decision_mode = decision_info.get("decision_mode")

                else:
                    continue

                master_record = build_master_db_record(
                    msg=msg,
                    info=info,
                    clean_body=clean_body,
                    assigned_team_key=assigned_team_key,
                    main_team=main_team,
                    sub_team=sub_team,
                    label_source=label_source,
                    task_id=task_id,
                    parent_id=parent_id,
                )

                audit_record = build_audit_raw_record(
                    msg=msg,
                    info=info,
                    clean_body=clean_body,
                    task_id=task_id,
                    parent_id=parent_id,
                )

                master_record["ml_confidence"] = ml_confidence
                master_record["decision_mode"] = decision_mode

                if parent_id not in parent_groups:
                    parent_groups[parent_id] = []

                parent_groups[parent_id].append({
                    "master_db": master_record,
                    "audit_raw": audit_record,
                })

                processed_tasks.add(task_id)

            except Exception as e:
                print(f"Error processing message: {e}")

        # =====================================================
        # APPLY CROSS TASK INFERENCE
        # =====================================================
        for parent_id, bundles in parent_groups.items():
            rows = [bundle["master_db"] for bundle in bundles]
            rows = apply_cross_task_inference(rows)
            sibling_count = len(rows)

            explicit_teams = [
                row["label_sub_team"]
                for row in rows
                if row["label_sub_team"] in ["AWS Team", "GCP Team"]
            ]
            sibling_known_sub_team = ",".join(sorted(set(explicit_teams))) if explicit_teams else None

            for bundle, row in zip(bundles, rows):
                bundle["master_db"] = row
                bundle["master_db"]["sibling_task_count"] = sibling_count
                bundle["master_db"]["sibling_known_sub_team"] = sibling_known_sub_team
                bundle["master_db"]["text_input"] = build_text_input(bundle["master_db"])

            for bundle in bundles:
                master_record = bundle["master_db"]
                audit_record = bundle["audit_raw"]
                conf_str = f"{master_record['ml_confidence']*100:.2f}%" if master_record['ml_confidence'] else "N/A"

                task_obj = {
                    "task": master_record["record_id"],
                    "ritm": master_record["parent_id"],
                    "short_desc": master_record["short_desc_clean"],
                    "env": master_record["related_env_raw"],
                    "final_route": master_record["label_sub_team"] if master_record["label_sub_team"] else master_record["label_main_team"],
                    "sent_date": master_record["email_date"],
                    "master_record": master_record,
                    "audit_record": audit_record,
                }

                all_tasks_list.append(task_obj)

                if save_to_db:
                    print(f"💾 save_to_db=True, inserting task {master_record.get('record_id')}")
                    save_master_and_audit_record(master_record, audit_record)
                else:
                    print(f"🧪 save_to_db=False, skip DB insert for task {master_record.get('record_id')}")

        all_tasks_list.sort(key=lambda x: x["sent_date"] or "")
        return all_tasks_list

    except Exception as e:
        print(f"IMAP Error: {e}")
        return []

    finally:
        if mail:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass