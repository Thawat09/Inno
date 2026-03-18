import os
import re
import email
import imaplib
import joblib
from datetime import datetime, timedelta
from app.services.llm_service import predict_with_ollama_rag
from app.config import Config
from model.export_to_csv import (
    decode_mime_words,
    extract_email_body,
    extract_ticket_info,
    identify_task_and_parent,
    get_ticket_type,
    detect_assigned_team_by_to,
    decide_cloud_subteam,
    apply_cross_task_inference,

    build_master_db_record,
    build_audit_raw_record,
    build_text_input,
    MASTER_DB_HEADERS,
    AUDIT_RAW_HEADERS,
)

from app.db.db_connection import db
from sqlalchemy import text


# =========================================================
# 1) LOAD ML MODEL
# =========================================================
ML_MODEL = None

try:
    model_path = Config.BEST_CLOUD_SUBTEAM_CLASSIFIER_MODEL_PATH
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
AWS_KEYWORDS = list(Config.AWS_KEYWORDS) + list(getattr(Config, "EXTRA_AWS_KEYWORDS", []))
GCP_KEYWORDS = list(Config.GCP_KEYWORDS) + list(getattr(Config, "EXTRA_GCP_KEYWORDS", []))


def safe_text(value):
    if value is None:
        return ""
    return str(value).strip()


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
    short_desc = safe_text(get_short_desc_from_info(info))
    related_env = safe_text(info.get("related_env"))
    description = safe_text(info.get("description"))
    ticket_type = safe_text(get_ticket_type(info))
    merged_header = f"{safe_text(subject)} || {short_desc}"
    merged_body = f"{related_env} || {description} || {safe_text(clean_body)}"
    rule_has_gcp_hub = int("GCP HUB" in merged_header.upper())
    rule_has_aws_hub = int("AWS HUB" in merged_header.upper())
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
    if ML_MODEL is None:
        print("⚠️ ML model unavailable")
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
            print(f"🤖 ML predicted: {predicted_label} | confidence={confidence:.4f} ({confidence*100:.2f}%)")
        else:
            print(f"🤖 ML predicted: {predicted_label} | confidence=N/A (no predict_proba)")

        return predicted_label, confidence, "ml_model"

    except Exception as e:
        print(f"⚠️ ML prediction failed: {e}")
        return None, None, "ml_model_error"


def decide_cloud_subteam_with_ml(info, clean_body, subject, to_address):
    logic_sub_team, logic_label_source, logic_extra = decide_cloud_subteam(
        info,
        clean_body,
        subject
    )

    explicit_logic_sources = {
        "task_short_desc_prefix",
        "ritm_short_desc_prefix",
        "subject_prefix",
        "task_short_desc_hub",
        "ip_match",
    }

    if logic_label_source in explicit_logic_sources:
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

    if (
        ml_sub_team in ["AWS Team", "GCP Team"]
        and ml_confidence is not None
        and ml_confidence >= threshold
    ):
        return ml_sub_team, f"{ml_source}_confidence_{ml_confidence:.4f}", {
            "decision_mode": "ml_high_confidence",
            "ml_used": True,
            "ml_confidence": ml_confidence,
            "logic_candidate": logic_sub_team,
            "logic_source": logic_label_source
        }

    if ml_confidence is not None:
        fallback_source = f"{logic_label_source}_fallback_ml_low_conf_{ml_confidence:.4f}"
        print(f"⚠️ Fallback to logic because ML confidence too low: {ml_confidence:.4f}")
    else:
        fallback_source = f"{logic_label_source}_fallback_ml_unavailable"
        print("⚠️ Fallback to logic because ML unavailable")

    return logic_sub_team, fallback_source, {
        "decision_mode": "logic_fallback",
        "ml_used": False,
        "ml_confidence": ml_confidence,
        "ml_candidate": ml_sub_team,
        "logic_candidate": logic_sub_team,
        "logic_source": logic_label_source
    }


def decide_cloud_subteam_with_rag(info, clean_body, subject, to_address, task_id=None):
    logic_sub_team, logic_label_source, logic_extra = decide_cloud_subteam(
        info,
        clean_body,
        subject
    )

    explicit_logic_sources = {
        "task_short_desc_prefix",
        "ritm_short_desc_prefix",
        "subject_prefix",
        "task_short_desc_hub",
        "ip_match",
    }

    if logic_label_source in explicit_logic_sources:
        return logic_sub_team, logic_label_source, {
            "decision_mode": "logic_explicit_rule",
            "ml_used": False,
            "ml_confidence": None,
            "rag_context_count": 0
        }

    text_for_ai = rebuild_text_input_for_email(info, clean_body, subject, to_address)
    rag_contexts = retrieve_rag_contexts(
        info=info,
        clean_body=clean_body,
        subject=subject,
        to_address=to_address,
        exclude_task_id=task_id
    )

    rag_predicted = predict_with_ollama_rag(text_for_ai, rag_contexts)

    valid_teams = ["AWS Team", "GCP Team", "GCP & AWS Team (Both)"]

    print(f"🤖 RAG predicted: {rag_predicted}")

    if rag_predicted in valid_teams:
        return rag_predicted, f"rag_{Config.LLM_MODEL_NAME}", {
            "decision_mode": "rag_prediction",
            "ml_used": False,
            "ml_confidence": 1.0,
            "logic_candidate": logic_sub_team,
            "logic_source": logic_label_source,
            "rag_context_count": len(rag_contexts)
        }

    print("⚠️ RAG invalid or unavailable, fallback to logic")

    return logic_sub_team, f"{logic_label_source}_fallback_rag_invalid", {
        "decision_mode": "logic_fallback_after_rag",
        "ml_used": False,
        "ml_confidence": None,
        "logic_candidate": logic_sub_team,
        "logic_source": logic_label_source,
        "rag_context_count": len(rag_contexts)
    }


def decide_cloud_subteam_runtime(info, clean_body, subject, to_address, task_id=None):
    if Config.LLM_ENABLED:
        print("🧠 Routing mode: RAG")
        return decide_cloud_subteam_with_rag(info, clean_body, subject, to_address, task_id=task_id)

    print("🤖 Routing mode: ML")
    return decide_cloud_subteam_with_ml(info, clean_body, subject, to_address)


# =========================================================
# 3) DB HELPERS
# =========================================================
def extract_ips_for_rag(text_value):
    if not text_value:
        return []
    return re.findall(r"\b(?:10\.41\.\d{1,3}\.\d{1,3}|10\.42\.\d{1,3}\.\d{1,3})\b", str(text_value))


def retrieve_rag_contexts(info, clean_body, subject, to_address, exclude_task_id=None):
    session = db.get_session()

    try:
        top_k = int(getattr(Config, "RAG_TOP_K", 5))

        short_desc = safe_text(get_short_desc_from_info(info))
        related_env = safe_text(info.get("related_env"))
        description = safe_text(info.get("description"))
        body_text = safe_text(clean_body)
        subject_text = safe_text(subject)

        merged_text = " || ".join([subject_text, short_desc, related_env, description, body_text])
        ips = extract_ips_for_rag(merged_text)

        has_aws_ip = 1 if "10.41." in merged_text else 0
        has_gcp_ip = 1 if "10.42." in merged_text else 0

        subject_like = f"%{subject_text[:120]}%" if subject_text else "%"
        short_desc_like = f"%{short_desc[:120]}%" if short_desc else "%"
        env_like = f"%{related_env[:120]}%" if related_env else "%"
        body_like = f"%{body_text[:120]}%" if body_text else "%"

        ip_like_1 = f"%{ips[0]}%" if len(ips) >= 1 else None
        ip_like_2 = f"%{ips[1]}%" if len(ips) >= 2 else None

        sql = text(f"""
            SELECT TOP {top_k}
                record_id,
                parent_id,
                label_sub_team,
                label_source,
                decision_mode,
                email_date,
                related_env_raw,
                subject_clean,
                short_desc_clean,
                description_clean,
                (
                    CASE
                        WHEN :related_env <> '' AND related_env_raw = :related_env THEN 50
                        WHEN :related_env <> '' AND related_env_raw LIKE :env_like THEN 25
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :subject_text <> '' AND subject_clean LIKE :subject_like THEN 20
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :short_desc <> '' AND short_desc_clean LIKE :short_desc_like THEN 20
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :body_text <> '' AND description_clean LIKE :body_like THEN 10
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :has_aws_ip = 1 AND has_aws_ip = 1 THEN 15
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :has_gcp_ip = 1 AND has_gcp_ip = 1 THEN 15
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :ip_like_1 IS NOT NULL AND body_for_model LIKE :ip_like_1 THEN 30
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN :ip_like_2 IS NOT NULL AND body_for_model LIKE :ip_like_2 THEN 30
                        ELSE 0
                    END
                ) AS retrieval_score
            FROM email_ticket_master
            WHERE label_sub_team IN ('AWS Team', 'GCP Team', 'GCP & AWS Team (Both)')
              AND (:exclude_task_id IS NULL OR record_id <> :exclude_task_id)
              AND (
                    (:related_env <> '' AND (related_env_raw = :related_env OR related_env_raw LIKE :env_like))
                    OR (:subject_text <> '' AND subject_clean LIKE :subject_like)
                    OR (:short_desc <> '' AND short_desc_clean LIKE :short_desc_like)
                    OR (:body_text <> '' AND description_clean LIKE :body_like)
                    OR (:has_aws_ip = 1 AND has_aws_ip = 1)
                    OR (:has_gcp_ip = 1 AND has_gcp_ip = 1)
                    OR (:ip_like_1 IS NOT NULL AND body_for_model LIKE :ip_like_1)
                    OR (:ip_like_2 IS NOT NULL AND body_for_model LIKE :ip_like_2)
              )
            ORDER BY retrieval_score DESC, email_date DESC
        """)

        rows = session.execute(sql, {
            "related_env": related_env,
            "env_like": env_like,
            "subject_text": subject_text,
            "subject_like": subject_like,
            "short_desc": short_desc,
            "short_desc_like": short_desc_like,
            "body_text": body_text,
            "body_like": body_like,
            "has_aws_ip": has_aws_ip,
            "has_gcp_ip": has_gcp_ip,
            "ip_like_1": ip_like_1,
            "ip_like_2": ip_like_2,
            "exclude_task_id": exclude_task_id,
        }).mappings().all()

        results = [dict(row) for row in rows if row.get("retrieval_score", 0) > 0]

        print(f"📚 RAG retrieved contexts: {len(results)}")
        for item in results:
            print(
                f"   - {item.get('record_id')} | "
                f"score={item.get('retrieval_score')} | "
                f"route={item.get('label_sub_team')}"
            )

        return results

    except Exception as e:
        print(f"⚠️ retrieve_rag_contexts error: {e}")
        return []

    finally:
        session.close()


def task_already_recorded(task_id):
    if not task_id:
        print("⚠️ task_already_recorded: task_id is empty")
        return False

    session = db.get_session()
    try:
        query = text("""
            SELECT TOP 1 record_id
            FROM email_ticket_master
            WHERE record_id = :record_id
        """)

        result = session.execute(query, {"record_id": task_id}).fetchone()

        if result is not None:
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ DB check error for task {task_id}: {e}")
        return False
    finally:
        session.close()


def should_send_task(task_id, processed_tasks):
    if not task_id:
        return False

    if task_already_recorded(task_id):
        return False

    if task_id in processed_tasks:
        return False

    return True


def filter_columns(record: dict, allowed_columns: list):
    return {k: record.get(k) for k in allowed_columns}


def save_master_and_audit_record(master_record, audit_record):
    session = db.get_session()

    try:
        master_allowed_columns = list(MASTER_DB_HEADERS) + ["ml_confidence", "decision_mode"]
        master_data = filter_columns(master_record, master_allowed_columns)
        audit_data = filter_columns(audit_record, AUDIT_RAW_HEADERS)
        master_cols = ", ".join(master_data.keys())
        master_params = ", ".join([f":{k}" for k in master_data.keys()])
        audit_cols = ", ".join(audit_data.keys())
        audit_params = ", ".join([f":{k}" for k in audit_data.keys()])

        master_sql = f"""
        INSERT INTO email_ticket_master ({master_cols})
        VALUES ({master_params})
        """

        audit_sql = f"""
        INSERT INTO email_ticket_audit_raw ({audit_cols})
        VALUES ({audit_params})
        """

        session.execute(text(master_sql), master_data)
        print(f"✅ MASTER insert executed for: {master_record.get('record_id')}")

        session.execute(text(audit_sql), audit_data)
        print(f"✅ AUDIT insert executed for: {master_record.get('record_id')}")

        session.commit()
        print(f"✅ Successfully committed: {master_record.get('record_id')}")
        print("=" * 100)

    except Exception as e:
        session.rollback()
        print(f"❌ DB Save Error for {master_record.get('record_id')}: {str(e)}")
        raise
    finally:
        session.close()


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
                print(f"🔍 Task: {master_record['record_id']} | Mode: {master_record['decision_mode']} | Conf: {conf_str} | Route: {master_record['label_sub_team']}")

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