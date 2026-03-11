# import email
# import imaplib
# from datetime import datetime, timedelta

# from app.config import Config
# from model.export_to_csv import (
#     decode_mime_words,
#     extract_email_body,
#     extract_ticket_info,
#     identify_task_and_parent,
#     get_ticket_type,
#     detect_assigned_team_by_to,
#     decide_cloud_subteam,
#     apply_cross_task_inference
# )

# # import DB connection
# from app.db.db_connection import db


# processed_tasks = set()


# def build_db_record(msg, info, clean_body, assigned_team_key, main_team, sub_team, label_source, task_id, parent_id):

#     subject_raw = decode_mime_words(msg.get("Subject", ""))
#     from_address = decode_mime_words(msg.get("From", ""))
#     to_address = decode_mime_words(msg.get("To", ""))

#     try:
#         sent_date = email.utils.parsedate_to_datetime(msg.get("Date"))
#     except:
#         sent_date = None

#     short_desc = (
#         info.get("task_short_desc")
#         or info.get("ritm_short_desc")
#         or info.get("inc_short_desc")
#         or info.get("ctask_short_desc")
#     )

#     return {
#         "task_id": task_id,
#         "parent_id": parent_id,
#         "ticket_type": get_ticket_type(info),
#         "message_id": msg.get("Message-ID"),
#         "email_date": sent_date,

#         "from_address": from_address,
#         "to_address": to_address,

#         "subject": subject_raw,
#         "short_desc": short_desc,
#         "description": info.get("description"),
#         "related_env": info.get("related_env"),
#         "clean_body": clean_body,

#         "request_number": info.get("request_number"),
#         "ritm_no": info.get("ritm_no"),
#         "task_no": info.get("task_no"),
#         "itask_no": info.get("itask_no"),
#         "ctask_no": info.get("ctask_no"),

#         "opened_by": info.get("opened_by"),
#         "requested_for": info.get("requested_for"),
#         "priority": info.get("priority"),

#         "ips": info.get("ips"),
#         "urls": info.get("urls"),

#         "assigned_group_from_to": assigned_team_key,
#         "label_main_team": main_team,
#         "label_sub_team": sub_team,
#         "label_source": label_source,

#         "sibling_task_count": 1,
#         "sibling_known_sub_team": None,
#         "cross_task_inference_used": False,
#     }


# def task_already_recorded(task_id):

#     """
#     ตรวจสอบว่า task นี้เคยถูกบันทึกใน DB หรือยัง

#     ตอนนี้ COMMENT ไว้ก่อน
#     """

#     # session = db.get_session()
#     #
#     # result = session.execute(
#     #     "SELECT task_id FROM email_tasks WHERE task_id = :task_id",
#     #     {"task_id": task_id}
#     # ).fetchone()
#     #
#     # session.close()
#     #
#     # return result is not None

#     return False


# def save_task_record(record):

#     """
#     บันทึกข้อมูลลง DB

#     ตอนนี้ COMMENT ไว้ก่อน
#     """

#     # session = db.get_session()
#     #
#     # session.execute(
#     #     """
#     #     INSERT INTO email_tasks (
#     #         task_id,
#     #         parent_id,
#     #         ticket_type,
#     #         subject,
#     #         short_desc,
#     #         label_main_team,
#     #         label_sub_team
#     #     )
#     #     VALUES (
#     #         :task_id,
#     #         :parent_id,
#     #         :ticket_type,
#     #         :subject,
#     #         :short_desc,
#     #         :label_main_team,
#     #         :label_sub_team
#     #     )
#     #     """,
#     #     record
#     # )
#     #
#     # session.commit()
#     # session.close()

#     pass


# def should_send_task(task_id):

#     if not task_id:
#         return False

#     # อนาคตใช้ DB
#     if task_already_recorded(task_id):
#         return False

#     # ตอนนี้ใช้ set ชั่วคราว
#     if task_id in processed_tasks:
#         return False

#     return True


# def fetch_and_group_tasks():
#     all_tasks_list = []
#     parent_groups = {}
#     mail = None

#     try:

#         mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=30)
#         mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
#         mail.select("scg")

#         since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")

#         status, messages = mail.search(None, f'(SINCE "{since_date}")')
#         ids = messages[0].split()

#         if not ids:
#             return []

#         for m_id in reversed(ids):

#             try:

#                 status, msg_data = mail.fetch(m_id, "(RFC822)")
#                 if status != "OK":
#                     continue

#                 msg = email.message_from_bytes(msg_data[0][1])

#                 from_address = decode_mime_words(msg.get("From", ""))
#                 to_address = decode_mime_words(msg.get("To", "")).lower()
#                 subject = decode_mime_words(msg.get("Subject", ""))

#                 if Config.TARGET_SENDER.lower() not in from_address.lower():
#                     continue

#                 clean_body = extract_email_body(msg)
#                 info = extract_ticket_info(clean_body, subject)

#                 task_id, parent_id = identify_task_and_parent(info)

#                 if not should_send_task(task_id):
#                     continue

#                 assigned_team_key = detect_assigned_team_by_to(to_address)

#                 if not assigned_team_key:
#                     continue

#                 if assigned_team_key == "iNET Network Team":

#                     main_team = "iNET Network Team"
#                     sub_team = None
#                     label_source = "to_address"

#                 elif assigned_team_key == "iNET Operation Team":

#                     main_team = "iNET Operation Team"
#                     sub_team = None
#                     label_source = "to_address"

#                 elif assigned_team_key == "iNET Cloud Support Team":

#                     main_team = "iNET Cloud Support Team"

#                     sub_team, label_source, _ = decide_cloud_subteam(
#                         info,
#                         clean_body,
#                         subject
#                     )

#                 else:
#                     continue

#                 db_record = build_db_record(
#                     msg,
#                     info,
#                     clean_body,
#                     assigned_team_key,
#                     main_team,
#                     sub_team,
#                     label_source,
#                     task_id,
#                     parent_id
#                 )

#                 if parent_id not in parent_groups:
#                     parent_groups[parent_id] = []

#                 parent_groups[parent_id].append(db_record)

#                 processed_tasks.add(task_id)

#             except Exception as e:
#                 print(f"Error processing message: {e}")

#         for parent_id, tasks in parent_groups.items():
#             task_rows = apply_cross_task_inference(tasks)
#             sibling_count = len(task_rows)

#             explicit_teams = [
#                 t["label_sub_team"]
#                 for t in tasks
#                 if t["label_sub_team"] in ["AWS Team", "GCP Team"]
#             ]
#             sibling_known_sub_team = ",".join(sorted(set(explicit_teams))) if explicit_teams else None

#             for row in tasks:
#                 row["sibling_task_count"] = sibling_count
#                 row["sibling_known_sub_team"] = sibling_known_sub_team

#                 task_obj = {
#                     "task": row["task_id"],
#                     "ritm": row["parent_id"],
#                     "short_desc": row["short_desc"],
#                     "env": row["related_env"],
#                     "final_route": row["label_sub_team"] if row["label_sub_team"] else row["label_main_team"],
#                     "sent_date": row["email_date"],
#                     "db_record": row
#                 }

#                 all_tasks_list.append(task_obj)

#                 # หลังส่งสำเร็จค่อยบันทึก DB
#                 # save_task_record(row)

#         all_tasks_list.sort(key=lambda x: x["sent_date"] or datetime.min)

#         mail.logout()

#         return all_tasks_list

#     except Exception as e:

#         print(f"IMAP Error: {e}")
#         return []

#     finally:

#         if mail:
#             try:
#                 mail.close()
#             except:
#                 pass

# TODO ---------------------------------------------------------- new

import os
import re
import email
import imaplib
import joblib

from datetime import datetime, timedelta

from app.config import Config
from model.export_to_csv import (
    decode_mime_words,
    extract_email_body,
    extract_ticket_info,
    identify_task_and_parent,
    get_ticket_type,
    detect_assigned_team_by_to,
    decide_cloud_subteam,
    apply_cross_task_inference
)

# import DB connection
from app.db.db_connection import db


processed_tasks = set()


# =========================================================
# 1) LOAD ML MODEL
# =========================================================
ML_MODEL = None

try:
    model_path = Config.BEST_TICKET_CLASSIFIER_MODEL_PATH
    if os.path.exists(model_path):
        ML_MODEL = joblib.load(model_path)
        print(f"✅ Loaded ML model: {model_path}")
    else:
        print(f"⚠️ ML model not found: {model_path}")
except Exception as e:
    print(f"⚠️ Load ML model failed: {e}")
    ML_MODEL = None


# =========================================================
# 2) ML / LOGIC HELPERS
# =========================================================
AWS_KEYWORDS = list(Config.AWS_KEYWORDS) + list(Config.EXTRA_AWS_KEYWORDS)
GCP_KEYWORDS = list(Config.GCP_KEYWORDS) + list(Config.EXTRA_GCP_KEYWORDS)


def safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_for_logic(text: str) -> str:
    text = safe_text(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()


def count_keyword_hits(text: str, keywords):
    if not text:
        return 0
    text_upper = text.upper()
    return sum(1 for k in keywords if str(k).upper() in text_upper)


def get_short_desc_from_info(info):
    return (
        info.get("task_short_desc")
        or info.get("ritm_short_desc")
        or info.get("inc_short_desc")
        or info.get("ctask_short_desc")
        or ""
    )


def rebuild_text_input_for_email(info, clean_body, subject, to_address):
    """
    ต้องให้ format ตรงกับตอน train model
    """
    return (
        "TICKET_TYPE: " + safe_text(get_ticket_type(info)) + " ||| " +
        "TO_ADDRESS: " + safe_text(to_address) + " ||| " +
        "SUBJECT: " + safe_text(subject) + " ||| " +
        "SHORT_DESC: " + safe_text(get_short_desc_from_info(info)) + " ||| " +
        "DETAIL: " + safe_text(info.get("description")) + " ||| " +
        "ENV: " + safe_text(info.get("related_env")) + " ||| " +
        "BODY: " + safe_text(clean_body)
    )


def build_logic_text_for_email(info, clean_body, subject, to_address):
    """
    สร้าง logic_text ให้รูปแบบใกล้กับตอน train
    เพราะ model ถูก train ด้วย combined_features = text_input + logic_text
    """
    short_desc = safe_text(get_short_desc_from_info(info))
    related_env = safe_text(info.get("related_env"))
    description = safe_text(info.get("description"))
    ticket_type = safe_text(get_ticket_type(info))

    merged_header = f"{safe_text(subject)} || {short_desc}"
    merged_body = f"{related_env} || {description} || {safe_text(clean_body)}"

    rule_has_gcp_hub = int("GCP HUB" in merged_header.upper())
    rule_has_aws_hub = int("AWS HUB" in merged_header.upper())
    rule_has_gcp_prefix = int("[GCP]" in merged_header.upper())
    rule_has_aws_prefix = int("[AWS]" in merged_header.upper())
    rule_has_gcp_ip = int("10.42." in merged_body)
    rule_has_aws_ip = int("10.41." in merged_body)

    gcp_kw_header_hits = count_keyword_hits(merged_header, GCP_KEYWORDS)
    aws_kw_header_hits = count_keyword_hits(merged_header, AWS_KEYWORDS)
    gcp_kw_body_hits = count_keyword_hits(merged_body, GCP_KEYWORDS)
    aws_kw_body_hits = count_keyword_hits(merged_body, AWS_KEYWORDS)

    logic_text = (
        "TICKET_TYPE=" + ticket_type + " || " +
        "TO=" + safe_text(to_address) + " || " +
        "SUBJECT=" + safe_text(subject) + " || " +
        "SHORT_DESC=" + short_desc + " || " +
        "ENV=" + related_env + " || " +
        "DESC=" + description + " || " +
        "BODY=" + safe_text(clean_body) + " || " +
        "RULE_GCP_HUB=" + str(rule_has_gcp_hub) + " || " +
        "RULE_AWS_HUB=" + str(rule_has_aws_hub) + " || " +
        "RULE_GCP_IP=" + str(rule_has_gcp_ip) + " || " +
        "RULE_AWS_IP=" + str(rule_has_aws_ip) + " || " +
        "GCP_HEADER_HITS=" + str(gcp_kw_header_hits) + " || " +
        "AWS_HEADER_HITS=" + str(aws_kw_header_hits) + " || " +
        "GCP_BODY_HITS=" + str(gcp_kw_body_hits) + " || " +
        "AWS_BODY_HITS=" + str(aws_kw_body_hits)
    )

    return logic_text


def predict_cloud_subteam_by_ml(info, clean_body, subject, to_address):
    """
    return:
        predicted_label, confidence, source
    """
    if ML_MODEL is None:
        return None, None, "ml_model_unavailable"

    try:
        text_input = rebuild_text_input_for_email(info, clean_body, subject, to_address)
        logic_text = build_logic_text_for_email(info, clean_body, subject, to_address)
        combined_text = text_input + " ||| " + logic_text

        predicted_label = ML_MODEL.predict([combined_text])[0]

        confidence = None
        if hasattr(ML_MODEL, "predict_proba"):
            probs = ML_MODEL.predict_proba([combined_text])[0]
            confidence = float(max(probs))

        # ⭐ PRINT DEBUG
        # print("\n================ ML PREDICTION =================")
        # print("SUBJECT:", subject)
        # print("SHORT DESC:", get_short_desc_from_info(info))
        # print("ENV:", info.get("related_env"))
        # print("ML PREDICT:", predicted_label)
        # print("ML CONFIDENCE:", confidence)
        # print("================================================")

        return predicted_label, confidence, "ml_model"

    except Exception as e:
        print(f"⚠️ ML prediction failed: {e}")
        return None, None, "ml_model_error"


def decide_cloud_subteam_with_ml(info, clean_body, subject, to_address):
    """
    ใช้ logic เดิมก่อน
    ถ้า logic เป็น explicit rule ที่ชัดมาก -> ใช้ logic ทันที
    ถ้าไม่ชัด -> ค่อยลอง ML
    ถ้า ML confidence สูง -> ใช้ ML
    ถ้า confidence ต่ำ -> fallback กลับ logic
    """
    logic_sub_team, logic_label_source, logic_extra = decide_cloud_subteam(
        info,
        clean_body,
        subject
    )

    # print("\n----------- LOGIC RESULT -----------")
    # print("SUBJECT:", subject)
    # print("LOGIC SUB TEAM:", logic_sub_team)
    # print("LOGIC SOURCE:", logic_label_source)

    # rule ที่เชื่อถือได้มาก ใช้ logic ทันที
    explicit_logic_sources = {
        "rule_prefix_aws",
        "rule_prefix_gcp",
        "rule_task_short_desc_aws_hub",
        "rule_task_short_desc_gcp_hub",
    }

    if logic_label_source in explicit_logic_sources:
        print("DECISION: LOGIC (explicit rule)")
        print("----------------------------------")

        return logic_sub_team, logic_label_source, {
            "decision_mode": "logic_explicit_rule",
            "ml_used": False,
            "ml_confidence": None
        }

    ml_sub_team, ml_confidence, ml_source = predict_cloud_subteam_by_ml(
        info,
        clean_body,
        subject,
        to_address
    )

    threshold = getattr(Config, "ML_CONFIDENCE_THRESHOLD", 0.95)

    print("ML RESULT:", ml_sub_team)
    print("ML CONFIDENCE:", ml_confidence)
    print("THRESHOLD:", threshold)


    if (
        ml_sub_team in ["AWS Team", "GCP Team"]
        and ml_confidence is not None
        and ml_confidence >= threshold
    ):
        print("DECISION: ML (high confidence)")
        print("----------------------------------")

        return ml_sub_team, f"{ml_source}_confidence_{ml_confidence:.4f}", {
            "decision_mode": "ml_high_confidence",
            "ml_used": True,
            "ml_confidence": ml_confidence,
            "logic_candidate": logic_sub_team,
            "logic_source": logic_label_source
        }

    # fallback logic
    print("DECISION: LOGIC (fallback from ML)")
    print("----------------------------------")

    if ml_confidence is not None:
        fallback_source = f"{logic_label_source}_fallback_ml_low_conf_{ml_confidence:.4f}"
    else:
        fallback_source = f"{logic_label_source}_fallback_ml_unavailable"

    return logic_sub_team, fallback_source, {
        "decision_mode": "logic_fallback",
        "ml_used": False,
        "ml_confidence": ml_confidence,
        "ml_candidate": ml_sub_team,
        "logic_candidate": logic_sub_team,
        "logic_source": logic_label_source
    }


# =========================================================
# 3) DB RECORD
# =========================================================
def build_db_record(
    msg,
    info,
    clean_body,
    assigned_team_key,
    main_team,
    sub_team,
    label_source,
    task_id,
    parent_id,
    ml_confidence=None,
    decision_mode=None
):

    subject_raw = decode_mime_words(msg.get("Subject", ""))
    from_address = decode_mime_words(msg.get("From", ""))
    to_address = decode_mime_words(msg.get("To", ""))

    try:
        sent_date = email.utils.parsedate_to_datetime(msg.get("Date"))
    except Exception:
        sent_date = None

    short_desc = get_short_desc_from_info(info)

    return {
        "task_id": task_id,
        "parent_id": parent_id,
        "ticket_type": get_ticket_type(info),
        "message_id": msg.get("Message-ID"),
        "email_date": sent_date,

        "from_address": from_address,
        "to_address": to_address,

        "subject": subject_raw,
        "short_desc": short_desc,
        "description": info.get("description"),
        "related_env": info.get("related_env"),
        "clean_body": clean_body,

        "request_number": info.get("request_number"),
        "ritm_no": info.get("ritm_no"),
        "task_no": info.get("task_no"),
        "itask_no": info.get("itask_no"),
        "ctask_no": info.get("ctask_no"),

        "opened_by": info.get("opened_by"),
        "requested_for": info.get("requested_for"),
        "priority": info.get("priority"),

        "ips": info.get("ips"),
        "urls": info.get("urls"),

        "assigned_group_from_to": assigned_team_key,
        "label_main_team": main_team,
        "label_sub_team": sub_team,
        "label_source": label_source,

        "ml_confidence": ml_confidence,
        "decision_mode": decision_mode,

        "sibling_task_count": 1,
        "sibling_known_sub_team": None,
        "cross_task_inference_used": False,
    }


# =========================================================
# 4) DB CHECK / SAVE
# =========================================================
def task_already_recorded(task_id):
    """
    ตรวจสอบว่า task นี้เคยถูกบันทึกใน DB หรือยัง

    ตอนนี้ COMMENT ไว้ก่อน
    """

    # session = db.get_session()
    #
    # result = session.execute(
    #     "SELECT task_id FROM email_tasks WHERE task_id = :task_id",
    #     {"task_id": task_id}
    # ).fetchone()
    #
    # session.close()
    #
    # return result is not None

    return False


def save_task_record(record):
    """
    บันทึกข้อมูลลง DB

    ตอนนี้ COMMENT ไว้ก่อน
    """

    # session = db.get_session()
    #
    # session.execute(
    #     """
    #     INSERT INTO email_tasks (
    #         task_id,
    #         parent_id,
    #         ticket_type,
    #         subject,
    #         short_desc,
    #         label_main_team,
    #         label_sub_team
    #     )
    #     VALUES (
    #         :task_id,
    #         :parent_id,
    #         :ticket_type,
    #         :subject,
    #         :short_desc,
    #         :label_main_team,
    #         :label_sub_team
    #     )
    #     """,
    #     record
    # )
    #
    # session.commit()
    # session.close()

    pass


def should_send_task(task_id):
    if not task_id:
        return False

    # อนาคตใช้ DB
    if task_already_recorded(task_id):
        return False

    # ตอนนี้ใช้ set ชั่วคราว
    if task_id in processed_tasks:
        return False

    return True


# =========================================================
# 5) MAIN FETCH
# =========================================================
def fetch_and_group_tasks():
    all_tasks_list = []
    parent_groups = {}
    mail = None

    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=30)
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        mail.select("scg")

        since_date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")

        status, messages = mail.search(None, f'(SINCE "{since_date}")')
        ids = messages[0].split()

        if not ids:
            return []

        for m_id in reversed(ids):
            try:
                status, msg_data = mail.fetch(m_id, "(RFC822)")
                if status != "OK":
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

                if not should_send_task(task_id):
                    continue

                assigned_team_key = detect_assigned_team_by_to(to_address)

                if not assigned_team_key:
                    continue

                ml_confidence = None
                decision_mode = None

                # -------------------------------------------------
                # CASE 1: Network Team
                # -------------------------------------------------
                if assigned_team_key == "iNET Network Team":
                    main_team = "iNET Network Team"
                    sub_team = None
                    label_source = "to_address"
                    decision_mode = "to_address_routing"

                # -------------------------------------------------
                # CASE 2: Operation Team
                # -------------------------------------------------
                elif assigned_team_key == "iNET Operation Team":
                    main_team = "iNET Operation Team"
                    sub_team = None
                    label_source = "to_address"
                    decision_mode = "to_address_routing"

                # -------------------------------------------------
                # CASE 3: Cloud Support Team
                # ใช้ logic + ML
                # -------------------------------------------------
                elif assigned_team_key == "iNET Cloud Support Team":
                    main_team = "iNET Cloud Support Team"

                    sub_team, label_source, decision_info = decide_cloud_subteam_with_ml(
                        info,
                        clean_body,
                        subject,
                        to_address
                    )

                    ml_confidence = decision_info.get("ml_confidence")
                    decision_mode = decision_info.get("decision_mode")

                else:
                    continue

                db_record = build_db_record(
                    msg=msg,
                    info=info,
                    clean_body=clean_body,
                    assigned_team_key=assigned_team_key,
                    main_team=main_team,
                    sub_team=sub_team,
                    label_source=label_source,
                    task_id=task_id,
                    parent_id=parent_id,
                    ml_confidence=ml_confidence,
                    decision_mode=decision_mode
                )

                if parent_id not in parent_groups:
                    parent_groups[parent_id] = []

                parent_groups[parent_id].append(db_record)

                processed_tasks.add(task_id)

            except Exception as e:
                print(f"Error processing message: {e}")

        # =====================================================
        # APPLY CROSS TASK INFERENCE
        # =====================================================
        for parent_id, tasks in parent_groups.items():
            task_rows = apply_cross_task_inference(tasks)
            sibling_count = len(task_rows)

            explicit_teams = [
                t["label_sub_team"]
                for t in tasks
                if t["label_sub_team"] in ["AWS Team", "GCP Team"]
            ]
            sibling_known_sub_team = ",".join(sorted(set(explicit_teams))) if explicit_teams else None

            for row in tasks:
                row["sibling_task_count"] = sibling_count
                row["sibling_known_sub_team"] = sibling_known_sub_team

                task_obj = {
                    "task": row["task_id"],
                    "ritm": row["parent_id"],
                    "short_desc": row["short_desc"],
                    "env": row["related_env"],
                    "final_route": row["label_sub_team"] if row["label_sub_team"] else row["label_main_team"],
                    "sent_date": row["email_date"],
                    "db_record": row
                }

                all_tasks_list.append(task_obj)

                # หลังส่งสำเร็จค่อยบันทึก DB
                # save_task_record(row)

        all_tasks_list.sort(key=lambda x: x["sent_date"] or datetime.min)

        mail.logout()
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