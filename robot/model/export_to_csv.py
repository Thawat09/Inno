import email
import imaplib
from datetime import datetime, timedelta

from app.config import Config
from app.builders.dataset_builder import (
    build_audit_raw_record,
    build_cloud_subteam_training_record,
    build_main_team_training_record,
    build_master_db_record,
    build_text_input,
    build_training_record,
)
from app.constants.export_headers import (
    AUDIT_RAW_HEADERS,
    MASTER_DB_HEADERS,
    TRAINING_CLOUD_SUBTEAM_HEADERS,
    TRAINING_HEADERS,
    TRAINING_MAIN_TEAM_HEADERS,
)
from app.parsers.ticket_parser import extract_ticket_info, identify_task_and_parent
from app.routing.team_router import (
    apply_cross_task_inference,
    decide_cloud_subteam,
    detect_assigned_team_by_to,
)
from app.utils.csv_utils import write_csv
from app.utils.extract_utils import extract_email_body
from app.utils.text_utils import decode_mime_words

# =========================================================
# 8) MAIN
# =========================================================
def run_export(save_to_db=True):
    processed_tasks = set()
    parent_groups = {}

    final_master_db_rows = []
    final_audit_raw_rows = []
    final_training_rows = []
    final_training_main_team_rows = []
    final_training_cloud_subteam_rows = []

    print(f"🚀 Starting Email Extraction (Last {Config.DAYS_BACK} days)...")

    if not Config.IMAP_SERVER:
        print("❌ IMAP_SERVER ยังไม่ได้ตั้งค่า")
        return

    if not Config.EMAIL_USER or not Config.EMAIL_PASS:
        print("❌ EMAIL_USER หรือ EMAIL_PASS ยังไม่ได้ตั้งค่า")
        return

    mail = None
    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=Config.IMAP_TIMEOUT)
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)

        select_status, _ = mail.select(Config.MAILBOX_FOLDER)
        if select_status != "OK":
            print(f"❌ ไม่สามารถเปิด mailbox folder: {Config.MAILBOX_FOLDER}")
            mail.logout()
            return

        since_date = (datetime.now() - timedelta(days=Config.DAYS_BACK)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since_date}")')

        if status != "OK":
            print("❌ ไม่สามารถค้นหาอีเมลได้")
            mail.logout()
            return

        ids = messages[0].split()
        if Config.MAX_EMAILS is not None:
            ids = ids[-Config.MAX_EMAILS:]

        print(f"📥 Found {len(ids)} emails to inspect")

        if not ids:
            print("ℹ️ ไม่พบเมลตามเงื่อนไข")
            mail.logout()
            return

        total_ids = len(ids)

        for idx, m_id in enumerate(reversed(ids), start=1):
            try:
                printable_id = m_id.decode() if isinstance(m_id, bytes) else str(m_id)
                print(f"📨 Fetching email {idx}/{total_ids} | ID={printable_id}")
                mail.noop()
                status, msg_data = mail.fetch(m_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    print(f"⚠️ Skip email {printable_id}: fetch returned empty or not OK")
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

                if not task_id:
                    continue

                if task_id in processed_tasks:
                    continue

                assigned_team_key = detect_assigned_team_by_to(to_address)
                if not assigned_team_key:
                    continue

                if assigned_team_key == "iNET Network Team":
                    main_team = "iNET Network Team"
                    sub_team = None
                    label_source = "to_address"
                elif assigned_team_key == "iNET Operation Team":
                    main_team = "iNET Operation Team"
                    sub_team = None
                    label_source = "to_address"
                elif assigned_team_key == "iNET Cloud Support Team":
                    main_team = "iNET Cloud Support Team"
                    sub_team, label_source, _ = decide_cloud_subteam(info, clean_body, subject)
                else:
                    continue

                master_db_row = build_master_db_record(
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

                audit_raw_row = build_audit_raw_record(
                    msg=msg,
                    info=info,
                    clean_body=clean_body,
                    task_id=task_id,
                    parent_id=parent_id,
                )

                if parent_id not in parent_groups:
                    parent_groups[parent_id] = []

                parent_groups[parent_id].append({
                    "master_db": master_db_row,
                    "audit_raw": audit_raw_row,
                })
                processed_tasks.add(task_id)

            except Exception as e:
                print(f"⚠️ Error message ID {m_id}: {e}")

        for parent_id, task_bundles in parent_groups.items():
            rows = [bundle["master_db"] for bundle in task_bundles]
            rows = apply_cross_task_inference(rows)
            sibling_count = len(rows)

            explicit_teams = [
                row["label_sub_team"]
                for row in rows
                if row["label_sub_team"] in ["GCP Team", "AWS Team"]
            ]

            sibling_known_sub_team = ",".join(sorted(set(explicit_teams))) if explicit_teams else None

            for bundle, row in zip(task_bundles, rows):
                bundle["master_db"] = row
                bundle["master_db"]["sibling_task_count"] = sibling_count
                bundle["master_db"]["sibling_known_sub_team"] = sibling_known_sub_team
                bundle["master_db"]["text_input"] = build_text_input(bundle["master_db"])

            for bundle in task_bundles:
                master_db_row = bundle["master_db"]
                audit_raw_row = bundle["audit_raw"]
                final_master_db_rows.append(master_db_row)
                final_audit_raw_rows.append(audit_raw_row)
                final_training_rows.append(build_training_record(master_db_row))
                final_training_main_team_rows.append(build_main_team_training_record(master_db_row))

                if master_db_row["label_main_team"] == "iNET Cloud Support Team":
                    final_training_cloud_subteam_rows.append(build_cloud_subteam_training_record(master_db_row))

        write_csv(Config.MASTER_DB_CSV_FILENAME, MASTER_DB_HEADERS, final_master_db_rows)
        write_csv(Config.AUDIT_RAW_CSV_FILENAME, AUDIT_RAW_HEADERS, final_audit_raw_rows)
        write_csv(Config.TRAINING_CSV_FILENAME, TRAINING_HEADERS, final_training_rows)
        write_csv(Config.TRAINING_MAIN_TEAM_CSV_FILENAME, TRAINING_MAIN_TEAM_HEADERS, final_training_main_team_rows)
        write_csv(Config.TRAINING_CLOUD_SUBTEAM_CSV_FILENAME, TRAINING_CLOUD_SUBTEAM_HEADERS, final_training_cloud_subteam_rows)

        mail.logout()
        print("✅ Done")

    except Exception as e:
        print(f"❌ Error: {e}")
        if mail:
            try:
                mail.logout()
            except Exception:
                pass


if __name__ == "__main__":
    run_export(save_to_db=True)
