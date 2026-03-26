from app.config import Config
from app.parsers.ticket_parser import get_ticket_type
from app.processors.content_cleaner import clean_body_for_training, summarize_for_web
from app.routing.team_router import build_feature_flags
from app.utils.text_utils import (
    bool_or_none,
    clean_subject,
    decode_mime_words,
    mask_ticket_ids,
    normalize_scalar,
    normalize_text_field,
    normalize_text_single_line,
    parse_email_date,
    to_json_array,
)


# =========================================================
# 5) DATASET BUILDERS
# =========================================================
def pick_short_desc(info):
    return (
        info.get("task_short_desc")
        or info.get("ritm_short_desc")
        or info.get("inc_short_desc")
        or info.get("ctask_short_desc")
    )


def build_text_input(row):
    parts = []

    def add(name, value):
        v = normalize_text_single_line(value)
        if v:
            parts.append(f"{name}: {v}")

    add("ticket_type", row.get("ticket_type"))
    add("to_address", row.get("to_address"))
    add("subject", row.get("subject_clean"))
    add("short_desc", row.get("short_desc_clean"))
    add("description", row.get("description_for_model"))
    add("related_env", row.get("related_env_raw"))
    add("business_service", row.get("business_service"))
    add("service_offering", row.get("service_offering"))
    add("body", row.get("body_for_model"))

    return " [SEP] ".join(parts) if parts else None


def build_master_db_record(msg, info, clean_body, assigned_team_key, main_team, sub_team, label_source, task_id, parent_id, cross_task_inference_used=False):
    subject_raw = decode_mime_words(msg.get("Subject", ""))
    from_address = decode_mime_words(msg.get("From", ""))
    to_address = decode_mime_words(msg.get("To", ""))

    ticket_type = get_ticket_type(info)
    subject_cleaned = clean_subject(subject_raw)

    short_desc_raw = pick_short_desc(info)
    short_desc_clean = normalize_text_single_line(mask_ticket_ids(short_desc_raw), max_len=Config.MAX_SHORT_DESC_LEN)

    description_raw = info.get("description")
    description_clean = summarize_for_web(mask_ticket_ids(description_raw), max_len=Config.MAX_DESCRIPTION_LEN)
    description_for_model = clean_body_for_training(description_raw)

    related_env_raw = normalize_text_single_line(info.get("related_env"), max_len=Config.MAX_RELATED_ENV_LEN)
    body_for_model = clean_body_for_training(clean_body)

    flags = build_feature_flags(info, clean_body, subject_raw)

    record = {
        "record_id": normalize_scalar(task_id, max_len=100),
        "parent_id": normalize_scalar(parent_id, max_len=100),
        "message_id": normalize_scalar(msg.get("Message-ID", ""), max_len=255),
        "email_date": parse_email_date(msg),

        "from_address": normalize_scalar(from_address, max_len=255),
        "to_address": normalize_scalar(to_address, max_len=255),
        "ticket_type": normalize_scalar(ticket_type, max_len=50),

        "request_number": normalize_scalar(info.get("request_number"), max_len=100),
        "ritm_no": normalize_scalar(info.get("ritm_no"), max_len=100),
        "inc_no": normalize_scalar(info.get("inc_no"), max_len=100),
        "itask_no": normalize_scalar(info.get("itask_no"), max_len=100),
        "ctask_no": normalize_scalar(info.get("ctask_no"), max_len=100),

        "subject_clean": subject_cleaned,
        "short_desc_clean": short_desc_clean,
        "description_clean": normalize_text_field(description_clean, max_len=Config.MAX_DESCRIPTION_LEN),
        "description_for_model": normalize_text_field(description_for_model, max_len=Config.MAX_BODY_MODEL_LEN),
        "related_env_raw": related_env_raw,
        "body_for_model": normalize_text_field(body_for_model, max_len=Config.MAX_BODY_MODEL_LEN),

        "opened_by": normalize_scalar(info.get("opened_by"), max_len=255),
        "requested_for": normalize_scalar(info.get("requested_for"), max_len=255),
        "raised_by": normalize_scalar(info.get("raised_by"), max_len=255),
        "business_service": normalize_scalar(info.get("business_service"), max_len=255),
        "service_offering": normalize_scalar(info.get("service_offering"), max_len=255),
        "priority": normalize_scalar(info.get("priority"), max_len=100),
        "urgency": normalize_scalar(info.get("urgency"), max_len=100),
        "impact": normalize_scalar(info.get("impact"), max_len=100),
        "contact_email": normalize_scalar(info.get("email_address"), max_len=255),

        "ip_list_json": to_json_array(info.get("ips")),
        "url_list_json": to_json_array(info.get("urls")),

        "has_aws_ip": bool_or_none(flags["has_aws_ip"]),
        "has_gcp_ip": bool_or_none(flags["has_gcp_ip"]),
        "has_aws_keyword_header": bool_or_none(flags["has_aws_keyword_header"]),
        "has_gcp_keyword_header": bool_or_none(flags["has_gcp_keyword_header"]),
        "has_aws_keyword_body": bool_or_none(flags["has_aws_keyword_body"]),
        "has_gcp_keyword_body": bool_or_none(flags["has_gcp_keyword_body"]),
        "has_aws_keyword_desc": bool_or_none(flags["has_aws_keyword_desc"]),
        "has_gcp_keyword_desc": bool_or_none(flags["has_gcp_keyword_desc"]),
        "env_has_aws": bool_or_none(flags["env_has_aws"]),
        "env_has_gcp": bool_or_none(flags["env_has_gcp"]),

        "assigned_group_from_to": normalize_scalar(assigned_team_key, max_len=255),
        "route_scope": "direct_team" if assigned_team_key in ["iNET Network Team", "iNET Operation Team"] else "cloud_subteam",

        "sibling_task_count": 1,
        "sibling_known_sub_team": None,
        "cross_task_inference_used": bool(cross_task_inference_used),

        "label_main_team": normalize_scalar(main_team, max_len=255),
        "label_sub_team": normalize_scalar(sub_team, max_len=255),
        "label_source": normalize_scalar(label_source, max_len=100),
        "text_input": None,
    }

    record["text_input"] = build_text_input(record)
    return record


def build_audit_raw_record(msg, info, clean_body, task_id, parent_id):
    subject_raw = decode_mime_words(msg.get("Subject", ""))
    return {
        "record_id": normalize_scalar(task_id, max_len=100),
        "parent_id": normalize_scalar(parent_id, max_len=100),
        "message_id": normalize_scalar(msg.get("Message-ID", ""), max_len=255),
        "email_date": parse_email_date(msg),
        "subject_raw": normalize_text_single_line(subject_raw, max_len=2000),
        "body_raw": normalize_text_single_line(clean_body, max_len=15000),
        "parsed_task_short_desc": normalize_text_single_line(info.get("task_short_desc"), max_len=2000),
        "parsed_ritm_short_desc": normalize_text_single_line(info.get("ritm_short_desc"), max_len=2000),
        "parsed_inc_short_desc": normalize_text_single_line(info.get("inc_short_desc"), max_len=2000),
        "parsed_ctask_short_desc": normalize_text_single_line(info.get("ctask_short_desc"), max_len=2000),
        "parsed_description": normalize_text_single_line(info.get("description"), max_len=8000),
        "parsed_related_env": normalize_text_single_line(info.get("related_env"), max_len=2000),
        "parsed_requested_for": normalize_scalar(info.get("requested_for"), max_len=255),
        "parsed_opened_by": normalize_scalar(info.get("opened_by"), max_len=255),
        "parsed_business_service": normalize_scalar(info.get("business_service"), max_len=255),
        "parsed_service_offering": normalize_scalar(info.get("service_offering"), max_len=255),
        "ip_list_json": to_json_array(info.get("ips")),
        "url_list_json": to_json_array(info.get("urls")),
    }


def build_training_record(master_record):
    return {
        "record_id": master_record.get("record_id"),
        "ticket_type": master_record.get("ticket_type"),
        "to_address": master_record.get("to_address"),
        "subject_clean": master_record.get("subject_clean"),
        "short_desc_clean": master_record.get("short_desc_clean"),
        "description_for_model": master_record.get("description_for_model"),
        "related_env_raw": master_record.get("related_env_raw"),
        "body_for_model": master_record.get("body_for_model"),
        "text_input": master_record.get("text_input"),
        "label_main_team": master_record.get("label_main_team"),
        "label_sub_team": master_record.get("label_sub_team"),
    }


def build_main_team_training_record(master_record):
    return {
        "record_id": master_record.get("record_id"),
        "ticket_type": master_record.get("ticket_type"),
        "to_address": master_record.get("to_address"),
        "subject_clean": master_record.get("subject_clean"),
        "short_desc_clean": master_record.get("short_desc_clean"),
        "related_env_raw": master_record.get("related_env_raw"),
        "text_input": (
            f"to_address: {master_record.get('to_address') or ''} [SEP] "
            f"ticket_type: {master_record.get('ticket_type') or ''} [SEP] "
            f"subject: {master_record.get('subject_clean') or ''}"
        ),
        "label_main_team": master_record.get("label_main_team"),
    }


def build_cloud_subteam_training_record(master_record):
    return {
        "record_id": master_record.get("record_id"),
        "ticket_type": master_record.get("ticket_type"),
        "to_address": master_record.get("to_address"),
        "subject_clean": master_record.get("subject_clean"),
        "short_desc_clean": master_record.get("short_desc_clean"),
        "description_for_model": master_record.get("description_for_model"),
        "related_env_raw": master_record.get("related_env_raw"),
        "body_for_model": master_record.get("body_for_model"),
        "text_input": master_record.get("text_input"),
        "label_sub_team": master_record.get("label_sub_team"),
    }
