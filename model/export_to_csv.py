import os
import imaplib
import email
import re
import csv
import socket
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from email.header import decode_header


# =========================================================
# 1) CONFIGURATION
# =========================================================
class Config:
    IMAP_SERVER = "onemail.one.th"
    EMAIL_USER = "thawat.me@inetms.co.th"
    EMAIL_PASS = "TQEAMMFMYJAPNAZN"

    TARGET_SENDER = "SCGTicketSystems@service-now.com"

    MASTER_CSV_FILENAME = "ticket_master_data.csv"
    TRAINING_CSV_FILENAME = "ticket_training_data.csv"
    TRAINING_MAIN_TEAM_CSV_FILENAME = "ticket_training_main_team.csv"
    TRAINING_CLOUD_SUBTEAM_CSV_FILENAME = "ticket_training_cloud_sub_team.csv"

    MAILBOX_FOLDER = "scg"
    DAYS_BACK = 365
    MAX_EMAILS = None
    IMAP_TIMEOUT = 30

    SYSTEM_MAPPING = {
        "justperformqas.scg.com": "AWS Team",
        "api-justperformqas.scg.com": "AWS Team",
        "tscpcl.outsystemsenterprise.com": "AWS Team",
        "lsp.com": "AWS Team",
        "scgbpc.scg.com": "AWS Team",
        "test-scgbpc.scg.com": "AWS Team",
        "mdm.scg.com": "AWS Team",
        "test-mdm.scg.com": "AWS Team",
        "dev-mdm.scg.com": "AWS Team",
        "swdwd.scg.com": "AWS Team",
        "swqwd.scg.com": "AWS Team",
        "swpwd.scg.com": "AWS Team",
        "e-hr.scg.co.th": "AWS Team",
        "uat-e-hr.scg.co.th": "AWS Team",
        "dev-e-hr.scg.co.th": "AWS Team",
        "ehr.scg.co.th": "AWS Team",
        "uat-hr.scg.co.th": "AWS Team",
        "dev-hr.scg.co.th": "AWS Team",
        "ehr-efm.scg.co.th": "AWS Team",
        "uat-hr-efm.scg.co.th": "AWS Team",
        "dev-hr-efm.scg.co.th": "AWS Team",
        "sandeeuat.scg.com": "AWS Team",
        "sandee.scg.com": "AWS Team",
        "scgchem-ecbqa.scg.com": "AWS Team",
        "ssdmsg.scg.com": "AWS Team",
        "ssqmsg.scg.com": "AWS Team",
        "sspmsg.scg.com": "AWS Team",
        "scc-awss4wd71.scg.com": "AWS Team",
        "scc-awss4wd01.scg.com": "AWS Team"
    }

    AWS_KEYWORDS = ["[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB", "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT", "ELB", "EKS", "ECS", "Phassakorn Seenil"]
    GCP_KEYWORDS = ["[GCP]", "GCP", "GCP Project", "GOOGLE", "GEMINI", "GOOGLE WORKSPACE", "GCP USER", "GCP user", "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDFUNCTIONS", "CLOUDRUN", "APPENGINE", "Cloud Run", "spoke01", "sharedservices-prd-rg"]

    DIRECT_TO_TEAM_MAP = {
        "scg-wifi@inetms.co.th": "iNET Network Team",
        "scgcloud@inetms.co.th": "iNET Operation Team",
        "inetmscloud@inetms.co.th": "iNET Cloud Support Team",
        "scg_cloud_inet01@scg.com": "iNET Cloud Support Team"
    }


# =========================================================
# 2) UTILS
# =========================================================
def decode_mime_words(text):
    if not text:
        return ""
    decoded_parts = decode_header(text)
    result = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(enc or "utf-8", errors="replace"))
            except Exception:
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def clean_html_to_text(text):
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator="\n")


def normalize_whitespace(text):
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def normalize_for_csv(text):
    if not text:
        return ""
    text = normalize_whitespace(text)
    return text.replace("\n", " | ").strip()


def clean_subject(subject):
    if not subject:
        return ""
    subject = decode_mime_words(subject)
    subject = re.sub(r"\bTASK\d+\b", "TASK_ID", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\bRITM\d+\b", "RITM_ID", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\bITASK\d+\b", "ITASK_ID", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\bCTASK\d+\b", "CTASK_ID", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\bREQ\d+\b", "REQ_ID", subject, flags=re.IGNORECASE)
    return normalize_for_csv(subject)


def clean_body_for_training(text):
    """
    เก็บเนื้อหาที่มีสาระจริง และลบ noise เช่น Click here แบบยืดหยุ่น
    """
    if not text:
        return ""

    text = normalize_whitespace(text)

    remove_patterns = [
        r"Click\s*here\s*to\s*view\s*the\s*request.*",
        r"Click\s*here\s*to\s*view\s*the\s*item.*",
        r"Click\s*here\s*to\s*view\s*the\s*task.*",
        r"Click\s*here\s*to\s*view\s*the\s*change\s*task\s*record.*",
        r"\*\*\*\s*Please\s*DO-NOT-REPLY\s*this\s*email.*",
        r"Ref:MSG\d+.*",
    ]

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        skip = False
        for pat in remove_patterns:
            if re.search(pat, line_strip, re.IGNORECASE):
                skip = True
                break

        if skip:
            continue

        cleaned_lines.append(line_strip)

    text = "\n".join(cleaned_lines)

    text = re.sub(r"\bTASK\d+\b", "TASK_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRITM\d+\b", "RITM_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bITASK\d+\b", "ITASK_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCTASK\d+\b", "CTASK_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bREQ\d+\b", "REQ_ID", text, flags=re.IGNORECASE)

    return normalize_for_csv(text)


def extract_email_body(msg):
    body_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition.lower():
                continue

            if content_type in ["text/plain", "text/html"]:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    if payload:
                        decoded = payload.decode(charset, errors="replace")
                        body_parts.append(decoded)
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            if payload:
                body_parts.append(payload.decode(charset, errors="replace"))
        except Exception:
            pass

    raw_body = "\n".join(body_parts)
    text_body = clean_html_to_text(raw_body)
    return normalize_whitespace(text_body)


def parse_email_date(msg):
    raw_date = msg.get("Date", "")
    return raw_date.strip()


def find_urls(text):
    if not text:
        return []
    return re.findall(r"https?://[^\s'\"<>]+", text, flags=re.IGNORECASE)


def find_ips(text):
    if not text:
        return []
    return re.findall(r"\b10\.(?:41|42)\.\d{1,3}\.\d{1,3}\b", text)


def bool_str(value):
    return "true" if value else "false"


def contains_any(text, keywords):
    if not text:
        return False
    text_upper = text.upper()
    for k in keywords:
        pattern = re.escape(k.upper())
        if re.search(rf"(?<!\w){pattern}(?!\w)", text_upper):
            return True
    return False


def safe_group(match, default="N/A"):
    if match:
        val = match.group(1).strip()
        return val if val else default
    return default


# =========================================================
# 3) PARSER
# =========================================================
def extract_ticket_info(body, subject=""):
    patterns = {
        "request_number": r"Request Number:\s*(REQ\d+)",
        "ritm_no": r"Service Request Number:\s*(RITM\d+)",
        "task_no": r"Task Number:\s*(TASK\d+)",
        "ritm_short_desc": r"Service Request Details:.*?Short Description:\s*(.*?)(?:\nDescription:|\nOpened Date:|$)",
        "task_short_desc": r"Catalog Task Details:.*?Short Description:\s*(.*?)(?:\nClick\s*here\s*to\s*view\s*the\s*task|\nState:|\nRef:MSG\d+|$)",
        "inc_no": r"Number:\s*(INC\d+)",
        "itask_no": r"Number:\s*(ITASK\d+)",
        "inc_short_desc": r"Short Description:\s*(.*?)(?:\nDescription:|$)",
        "ctask_no": r"Number:\s*(CTASK\d+)",
        "ctask_short_desc": r"Short Description:\s*(.*?)(?:\nClick\s*here\s*to\s*view\s*the\s*change\s*task\s*record|\nDescription:|\nRef:MSG\d+|$)",
        "state": r"Catalog Task Details:.*?State:\s*([A-Za-z\s]+)",
        "related_env": r"Related environment:\s*(.*?)(?:\nState:|\nRef\. Case No\.|\nไฟล์ที่เกี่ยวข้อง|\nFile|\nติดต่อคุณ|$)",
        "description": r"Description:\s*(.*?)(?:\nRelated environment:|$)",
    }

    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
        results[key] = safe_group(match)

    results["urls"] = find_urls(body)
    results["ips"] = find_ips(body)

    subject_decoded = decode_mime_words(subject)

    is_ritm_assign = (
        "Catalog Task Assignment" in subject_decoded
        or "A Catalog Task record has been assigned" in body
        or re.search(r"Catalog Task\s+TASK\d+\s+has been assigned", subject_decoded, re.IGNORECASE)
    )

    is_itask_assign = (
        "Incident Task Assignment" in subject_decoded
        or "A Incident Task record has been assigned" in body
        or re.search(r"Incident task\s+ITASK\d+\s+has been assigned", subject_decoded, re.IGNORECASE)
    )

    is_ctask_assign = (
        "Change task" in subject_decoded
        or "A Change Task record has been assigned" in body
        or re.search(r"Change task\s+CTASK\d+\s+has been assigned", subject_decoded, re.IGNORECASE)
    )

    current_state = (results["state"] or "").lower()
    is_assigned_state = ("assigned" in current_state) or (results["state"] == "N/A")

    results["is_valid_ritm"] = bool(is_ritm_assign and is_assigned_state)
    results["is_valid_itask"] = bool(is_itask_assign)
    results["is_valid_ctask"] = bool(is_ctask_assign)

    return results


def get_ticket_type(info):
    if info["is_valid_ritm"]:
        return "catalog_task"
    if info["is_valid_itask"]:
        return "incident_task"
    if info["is_valid_ctask"]:
        return "change_task"
    return "unknown"


def identify_task_and_parent(info):
    current_task_id = "N/A"
    parent_id = "N/A"
    short_desc = "N/A"

    if info["is_valid_itask"]:
        current_task_id = info["itask_no"]
        parent_id = info["itask_no"]
        short_desc = info["inc_short_desc"]

    elif info["is_valid_ritm"]:
        current_task_id = info["task_no"]
        parent_id = info["ritm_no"]
        short_desc = info["task_short_desc"]

    elif info["is_valid_ctask"]:
        current_task_id = info["ctask_no"]
        parent_id = info["ctask_no"]
        short_desc = info["ctask_short_desc"]

    return current_task_id, parent_id, short_desc


# =========================================================
# 4) ROUTING LOGIC
# =========================================================
def detect_assigned_team_by_to(to_address):
    to_address = (to_address or "").lower()
    for email_addr, team_name in Config.DIRECT_TO_TEAM_MAP.items():
        if email_addr in to_address:
            return team_name
    return None


def build_feature_flags(info, clean_body, subject=""):
    full_content = (clean_body or "").upper()
    related_env = (info.get("related_env") or "").upper()
    task_short_desc = (info.get("task_short_desc") or "").upper()
    ritm_short_desc = (info.get("ritm_short_desc") or "").upper()
    description = (info.get("description") or "").upper()
    subject_upper = (subject or "").upper()

    has_aws_ip = any(ip.startswith("10.41.") for ip in info.get("ips", []))
    has_gcp_ip = any(ip.startswith("10.42.") for ip in info.get("ips", []))

    combined_headers = f"{subject_upper} {task_short_desc} {ritm_short_desc}"
    header_plus_desc = f"{subject_upper} {ritm_short_desc} {description}"

    has_aws_keyword_header = contains_any(combined_headers, Config.AWS_KEYWORDS)
    has_gcp_keyword_header = contains_any(combined_headers, Config.GCP_KEYWORDS)

    has_aws_keyword_body = contains_any(full_content, Config.AWS_KEYWORDS)
    has_gcp_keyword_body = contains_any(full_content, Config.GCP_KEYWORDS)

    has_aws_keyword_desc = contains_any(header_plus_desc, Config.AWS_KEYWORDS)
    has_gcp_keyword_desc = contains_any(header_plus_desc, Config.GCP_KEYWORDS)

    env_has_aws = "AWS" in related_env
    env_has_gcp = "GCP" in related_env or "GOOGLE" in related_env

    return {
        "has_aws_ip": has_aws_ip,
        "has_gcp_ip": has_gcp_ip,
        "has_aws_keyword_header": has_aws_keyword_header,
        "has_gcp_keyword_header": has_gcp_keyword_header,
        "has_aws_keyword_body": has_aws_keyword_body,
        "has_gcp_keyword_body": has_gcp_keyword_body,
        "has_aws_keyword_desc": has_aws_keyword_desc,
        "has_gcp_keyword_desc": has_gcp_keyword_desc,
        "env_has_aws": env_has_aws,
        "env_has_gcp": env_has_gcp,
    }


def decide_cloud_subteam(info, clean_body, subject):
    full_text = f"{subject} {clean_body}".upper()
    flags = build_feature_flags(info, clean_body, subject)

    if "[GCP]" in full_text:
        return "GCP Team", "hard_rule_gcp_prefix", flags

    if "[AWS]" in full_text:
        return "AWS Team", "hard_rule_aws_prefix", flags
    
    flags = build_feature_flags(info, clean_body, subject)

    if flags["has_aws_ip"] and not flags["has_gcp_ip"]:
        return "AWS Team", "ip_match", flags
    if flags["has_gcp_ip"] and not flags["has_aws_ip"]:
        return "GCP Team", "ip_match", flags

    urls = info.get("urls", [])
    for url in urls:
        url_lower = url.lower()
        for domain, team in Config.SYSTEM_MAPPING.items():
            if domain.lower() in url_lower:
                return team, "url_match", flags

    if flags["has_gcp_keyword_header"] and not flags["has_aws_keyword_header"]:
        return "GCP Team", "keyword_header", flags
    if flags["has_aws_keyword_header"] and not flags["has_gcp_keyword_header"]:
        return "AWS Team", "keyword_header", flags

    if (flags["env_has_gcp"] or flags["has_gcp_keyword_body"]) and not (flags["env_has_aws"] or flags["has_aws_keyword_body"]):
        return "GCP Team", "keyword_body_env", flags
    if (flags["env_has_aws"] or flags["has_aws_keyword_body"]) and not (flags["env_has_gcp"] or flags["has_gcp_keyword_body"]):
        return "AWS Team", "keyword_body_env", flags

    if flags["has_gcp_keyword_desc"] and not flags["has_aws_keyword_desc"]:
        return "GCP Team", "keyword_desc", flags
    if flags["has_aws_keyword_desc"] and not flags["has_gcp_keyword_desc"]:
        return "AWS Team", "keyword_desc", flags

    return "GCP & AWS Team (Both)", "fallback_both", flags


# =========================================================
# 5) DATASET BUILDER
# =========================================================
def build_text_input(row):
    parts = [
        f"ticket_type: {row.get('ticket_type', '')}",
        f"to_address: {row.get('to_address', '')}",
        f"assigned_group_from_to: {row.get('assigned_group_from_to', '')}",
        f"route_scope: {row.get('route_scope', '')}",
        f"subject: {row.get('subject_clean', '')}",
        f"task_short_desc: {row.get('task_short_desc', '')}",
        f"ritm_short_desc: {row.get('ritm_short_desc', '')}",
        f"description: {row.get('description', '')}",
        f"related_env: {row.get('related_env_raw', '')}",
        f"body_text: {row.get('body_text_clean', '')}",
    ]
    return " ||| ".join([p for p in parts if p.strip()])


def build_master_record(msg, info, clean_body, assigned_team_key, main_team, sub_team, label_source, task_id, parent_id, cross_task_inference_used=False):
    subject_raw = decode_mime_words(msg.get("Subject", ""))
    from_address = decode_mime_words(msg.get("From", ""))
    to_address = decode_mime_words(msg.get("To", ""))

    ticket_type = get_ticket_type(info)
    subject_cleaned = clean_subject(subject_raw)
    body_text_clean = clean_body_for_training(clean_body)

    flags = build_feature_flags(info, clean_body, subject_raw)

    record = {
        "message_id": normalize_for_csv(msg.get("Message-ID", "")),
        "email_date": normalize_for_csv(parse_email_date(msg)),
        "from_address": normalize_for_csv(from_address),
        "to_address": normalize_for_csv(to_address),
        "ticket_type": ticket_type,

        "task_id": task_id,
        "parent_id": parent_id,
        "request_number": normalize_for_csv(info.get("request_number", "N/A")),
        "ritm_no": normalize_for_csv(info.get("ritm_no", "N/A")),
        "inc_no": normalize_for_csv(info.get("inc_no", "N/A")),
        "itask_no": normalize_for_csv(info.get("itask_no", "N/A")),
        "ctask_no": normalize_for_csv(info.get("ctask_no", "N/A")),

        "subject_raw": normalize_for_csv(subject_raw),
        "subject_clean": subject_cleaned,

        "task_short_desc": normalize_for_csv(info.get("task_short_desc", "N/A")),
        "ritm_short_desc": normalize_for_csv(info.get("ritm_short_desc", "N/A")),
        "inc_short_desc": normalize_for_csv(info.get("inc_short_desc", "N/A")),
        "ctask_short_desc": normalize_for_csv(info.get("ctask_short_desc", "N/A")),
        "description": normalize_for_csv(info.get("description", "N/A")),
        "related_env_raw": normalize_for_csv(info.get("related_env", "N/A")),

        "body_text_clean": body_text_clean,

        "ip_list": "|".join(info.get("ips", [])),
        "url_list": "|".join(info.get("urls", [])),

        "has_aws_ip": bool_str(flags["has_aws_ip"]),
        "has_gcp_ip": bool_str(flags["has_gcp_ip"]),
        "has_aws_keyword_header": bool_str(flags["has_aws_keyword_header"]),
        "has_gcp_keyword_header": bool_str(flags["has_gcp_keyword_header"]),
        "has_aws_keyword_body": bool_str(flags["has_aws_keyword_body"]),
        "has_gcp_keyword_body": bool_str(flags["has_gcp_keyword_body"]),
        "has_aws_keyword_desc": bool_str(flags["has_aws_keyword_desc"]),
        "has_gcp_keyword_desc": bool_str(flags["has_gcp_keyword_desc"]),
        "env_has_aws": bool_str(flags["env_has_aws"]),
        "env_has_gcp": bool_str(flags["env_has_gcp"]),

        "assigned_group_from_to": assigned_team_key or "N/A",
        "route_scope": "direct_team" if assigned_team_key in ["iNET Network Team", "iNET Operation Team"] else "cloud_subteam",
        "sibling_task_count": 1,
        "sibling_known_sub_team": "N/A",
        "cross_task_inference_used": bool_str(cross_task_inference_used),

        "label_main_team": main_team,
        "label_sub_team": sub_team,
        "label_source": label_source,
        "text_input": "",
    }

    record["text_input"] = build_text_input(record)
    return record


def build_training_record(master_record):
    return {
        "record_id": master_record.get("task_id", ""),
        "ticket_type": master_record.get("ticket_type", ""),
        "to_address": master_record.get("to_address", ""),
        "subject_clean": master_record.get("subject_clean", ""),
        "task_short_desc": master_record.get("task_short_desc", ""),
        "ritm_short_desc": master_record.get("ritm_short_desc", ""),
        "description": master_record.get("description", ""),
        "related_env_raw": master_record.get("related_env_raw", ""),
        "body_text_clean": master_record.get("body_text_clean", ""),
        "text_input": master_record.get("text_input", ""),
        "label_main_team": master_record.get("label_main_team", ""),
        "label_sub_team": master_record.get("label_sub_team", ""),
    }


def build_main_team_training_record(master_record):
    return {
        "record_id": master_record.get("task_id", ""),
        "ticket_type": master_record.get("ticket_type", ""),
        "to_address": master_record.get("to_address", ""),
        "subject_clean": master_record.get("subject_clean", ""),
        "task_short_desc": master_record.get("task_short_desc", ""),
        "ritm_short_desc": master_record.get("ritm_short_desc", ""),
        "description": master_record.get("description", ""),
        "related_env_raw": master_record.get("related_env_raw", ""),
        "body_text_clean": master_record.get("body_text_clean", ""),
        "text_input": master_record.get("text_input", ""),
        "label_main_team": master_record.get("label_main_team", ""),
    }


def build_cloud_subteam_training_record(master_record):
    return {
        "record_id": master_record.get("task_id", ""),
        "ticket_type": master_record.get("ticket_type", ""),
        "to_address": master_record.get("to_address", ""),
        "subject_clean": master_record.get("subject_clean", ""),
        "task_short_desc": master_record.get("task_short_desc", ""),
        "ritm_short_desc": master_record.get("ritm_short_desc", ""),
        "description": master_record.get("description", ""),
        "related_env_raw": master_record.get("related_env_raw", ""),
        "body_text_clean": master_record.get("body_text_clean", ""),
        "text_input": master_record.get("text_input", ""),
        "label_sub_team": master_record.get("label_sub_team", ""),
    }


# =========================================================
# 6) CSV HEADERS
# =========================================================
MASTER_HEADERS = [
    "message_id",
    "email_date",
    "from_address",
    "to_address",
    "ticket_type",
    "task_id",
    "parent_id",
    "request_number",
    "ritm_no",
    "inc_no",
    "itask_no",
    "ctask_no",
    "subject_raw",
    "subject_clean",
    "task_short_desc",
    "ritm_short_desc",
    "inc_short_desc",
    "ctask_short_desc",
    "description",
    "related_env_raw",
    "body_text_clean",
    "ip_list",
    "url_list",
    "has_aws_ip",
    "has_gcp_ip",
    "has_aws_keyword_header",
    "has_gcp_keyword_header",
    "has_aws_keyword_body",
    "has_gcp_keyword_body",
    "has_aws_keyword_desc",
    "has_gcp_keyword_desc",
    "env_has_aws",
    "env_has_gcp",
    "assigned_group_from_to",
    "route_scope",
    "sibling_task_count",
    "sibling_known_sub_team",
    "cross_task_inference_used",
    "label_main_team",
    "label_sub_team",
    "label_source",
    "text_input",
]

TRAINING_HEADERS = [
    "record_id",
    "ticket_type",
    "to_address",
    "subject_clean",
    "task_short_desc",
    "ritm_short_desc",
    "description",
    "related_env_raw",
    "body_text_clean",
    "text_input",
    "label_main_team",
    "label_sub_team",
]

TRAINING_MAIN_TEAM_HEADERS = [
    "record_id",
    "ticket_type",
    "to_address",
    "subject_clean",
    "task_short_desc",
    "ritm_short_desc",
    "description",
    "related_env_raw",
    "body_text_clean",
    "text_input",
    "label_main_team",
]

TRAINING_CLOUD_SUBTEAM_HEADERS = [
    "record_id",
    "ticket_type",
    "to_address",
    "subject_clean",
    "task_short_desc",
    "ritm_short_desc",
    "description",
    "related_env_raw",
    "body_text_clean",
    "text_input",
    "label_sub_team",
]


# =========================================================
# 7) FILE WRITER
# =========================================================
def write_csv(filename, headers, rows):
    if not rows:
        print(f"ℹ️ No rows to write for {filename}")
        return

    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Exported {len(rows)} rows to {filename}")


# =========================================================
# 8) MAIN
# =========================================================
def run_export():
    processed_tasks = set()
    parent_groups = {}
    final_master_rows = []
    final_training_rows = []
    final_training_main_team_rows = []
    final_training_cloud_subteam_rows = []

    print(f"🚀 Starting Email Extraction (Last {Config.DAYS_BACK} days)...")

    if not Config.EMAIL_USER or not Config.EMAIL_PASS:
        print("❌ EMAIL_USER หรือ EMAIL_PASS ยังไม่ได้ตั้งค่าใน environment variables")
        return

    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=Config.IMAP_TIMEOUT)
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        mail.select(Config.MAILBOX_FOLDER)

        since_date = (datetime.now() - timedelta(days=Config.DAYS_BACK)).strftime("%d-%b-%Y")
        status, messages = mail.search(
            None,
            f'(SINCE "{since_date}" FROM "{Config.TARGET_SENDER}")'
        )

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

                task_id, parent_id, _ = identify_task_and_parent(info)

                if task_id == "N/A" or task_id in processed_tasks:
                    continue

                assigned_team_key = detect_assigned_team_by_to(to_address)
                if not assigned_team_key:
                    continue

                if assigned_team_key == "iNET Network Team":
                    main_team = "iNET Network Team"
                    sub_team = "NONE"
                    label_source = "to_address"

                elif assigned_team_key == "iNET Operation Team":
                    main_team = "iNET Operation Team"
                    sub_team = "NONE"
                    label_source = "to_address"

                elif assigned_team_key == "iNET Cloud Support Team":
                    main_team = "iNET Cloud Support Team"
                    sub_team, label_source, _ = decide_cloud_subteam(info, clean_body, subject)

                else:
                    continue

                master_row = build_master_record(
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

                if parent_id not in parent_groups:
                    parent_groups[parent_id] = []

                parent_groups[parent_id].append(master_row)
                processed_tasks.add(task_id)

            except Exception as e:
                print(f"⚠️ Error message ID {m_id}: {e}")

        for parent_id, tasks in parent_groups.items():
            sibling_count = len(tasks)

            known_team = next(
                (t["label_sub_team"] for t in tasks if t["label_sub_team"] in ["GCP Team", "AWS Team"]),
                None
            )

            sibling_known_sub_team = known_team if known_team else "N/A"

            if sibling_count > 1 and known_team:
                for t in tasks:
                    if t["label_sub_team"] == "GCP & AWS Team (Both)":
                        t["label_sub_team"] = known_team
                        t["label_source"] = "cross_task_inference"
                        t["cross_task_inference_used"] = "true"

            for t in tasks:
                t["sibling_task_count"] = sibling_count
                t["sibling_known_sub_team"] = sibling_known_sub_team
                t["text_input"] = build_text_input(t)

                final_master_rows.append(t)

                full_training_row = build_training_record(t)
                final_training_rows.append(full_training_row)

                main_team_training_row = build_main_team_training_record(t)
                final_training_main_team_rows.append(main_team_training_row)

                if t["label_main_team"] == "iNET Cloud Support Team":
                    cloud_subteam_training_row = build_cloud_subteam_training_record(t)
                    final_training_cloud_subteam_rows.append(cloud_subteam_training_row)

        write_csv(Config.MASTER_CSV_FILENAME, MASTER_HEADERS, final_master_rows)
        write_csv(Config.TRAINING_CSV_FILENAME, TRAINING_HEADERS, final_training_rows)
        write_csv(Config.TRAINING_MAIN_TEAM_CSV_FILENAME, TRAINING_MAIN_TEAM_HEADERS, final_training_main_team_rows)
        write_csv(
            Config.TRAINING_CLOUD_SUBTEAM_CSV_FILENAME,
            TRAINING_CLOUD_SUBTEAM_HEADERS,
            final_training_cloud_subteam_rows
        )

        mail.logout()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    run_export()