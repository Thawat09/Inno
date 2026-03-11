import csv
import email
import imaplib
import ipaddress
import json
import re
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from app.config import Config

# =========================================================
# 1) UTILS
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


def clean_unicode_spaces(text):
    if text is None:
        return None
    text = str(text)
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = text.replace("●", "")
    return text


def normalize_scalar(text, max_len=None):
    if text is None:
        return None
    text = clean_unicode_spaces(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    if max_len:
        text = text[:max_len]
    return text


def normalize_text_field(text, max_len=None):
    if text is None:
        return None

    text = clean_unicode_spaces(text)
    text = text.replace("\r", "\n")

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        line = line.strip("|").strip()
        if line:
            lines.append(line)

    text = "\n".join(lines).strip()
    if not text:
        return None

    if max_len:
        text = text[:max_len]

    return text


def normalize_text_single_line(text, max_len=None):
    text = normalize_text_field(text, max_len=max_len)
    if text is None:
        return None
    return text.replace("\n", " | ")


def clean_html_to_text(text):
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator="\n")


def parse_email_date(msg):
    raw_date = msg.get("Date", "")
    try:
        dt = parsedate_to_datetime(raw_date)
        return dt.isoformat()
    except Exception:
        return normalize_scalar(raw_date, max_len=100)


def bool_or_none(value):
    if value is None:
        return None
    return bool(value)


def to_json_array(values):
    if not values:
        return None
    cleaned = []
    for v in values:
        nv = normalize_scalar(v)
        if nv:
            cleaned.append(nv)
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


def find_urls(text):
    if not text:
        return []
    return list(dict.fromkeys(re.findall(r"https?://[^\s'\"<>]+", text, flags=re.IGNORECASE)))


def find_ips(text):
    if not text:
        return []

    candidates = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    valid = []
    for ip in candidates:
        try:
            ipaddress.ip_address(ip)
            valid.append(ip)
        except ValueError:
            continue

    return list(dict.fromkeys(valid))


def contains_any(text, keywords):
    if not text:
        return False
    text_upper = text.upper()
    for k in keywords:
        pattern = re.escape(k.upper())
        if re.search(rf"(?<!\w){pattern}(?!\w)", text_upper):
            return True
    return False


def mask_ticket_ids(text):
    if not text:
        return text
    text = re.sub(r"\bTASK\d+\b", "TASK_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRITM\d+\b", "RITM_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bITASK\d+\b", "ITASK_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bCTASK\d+\b", "CTASK_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bREQ\d+\b", "REQ_ID", text, flags=re.IGNORECASE)
    text = re.sub(r"\bINC\d+\b", "INC_ID", text, flags=re.IGNORECASE)
    return text


def _decode_part_payload(part):
    try:
        payload = part.get_payload(decode=True)
        charset = part.get_content_charset() or "utf-8"
        if payload:
            return payload.decode(charset, errors="replace")
    except Exception:
        return None
    return None


def extract_email_body(msg):
    plain_parts = []
    html_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", "")).lower()

            if "attachment" in disposition:
                continue

            if content_type == "text/plain":
                decoded = _decode_part_payload(part)
                if decoded:
                    plain_parts.append(decoded)

            elif content_type == "text/html":
                decoded = _decode_part_payload(part)
                if decoded:
                    html_parts.append(decoded)
    else:
        content_type = msg.get_content_type()
        decoded = _decode_part_payload(msg)
        if decoded:
            if content_type == "text/plain":
                plain_parts.append(decoded)
            else:
                html_parts.append(decoded)

    if plain_parts:
        raw_body = "\n".join(plain_parts)
        return normalize_text_field(raw_body)

    if html_parts:
        raw_body = "\n".join(html_parts)
        text_body = clean_html_to_text(raw_body)
        return normalize_text_field(text_body)

    return None


def clean_subject(subject):
    if not subject:
        return None
    subject = decode_mime_words(subject)
    subject = mask_ticket_ids(subject)
    return normalize_text_single_line(subject, max_len=Config.MAX_SUBJECT_LEN)


def extract_first_by_pattern(text, pattern):
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def extract_catalog_task_short_desc(body):
    if not body:
        return None

    patterns = [
        r"Catalog Task Details:.*?Short Description:\s*(.*?)\s*Click here to view the task",
        r"Catalog Task Details:.*?Short Description:\s*(.*?)(?:\n[A-Za-z][A-Za-z /()._-]*:|$)",
        r"Short Description:\s*(Firewall Request\s*:\s*(?:AWS|GCP)\s*Hub)",
    ]

    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = normalize_text_single_line(match.group(1))
            if value:
                return value

    return None


def detect_hub_from_text(text):
    if not text:
        return None

    text_upper = text.upper()

    if "GCP HUB" in text_upper:
        return "GCP Team"

    if "AWS HUB" in text_upper:
        return "AWS Team"

    return None


def contains_any_loose(text, keywords):
    if not text:
        return False
    text_upper = text.upper()
    return any(str(k).upper() in text_upper for k in keywords)


def extract_section_text(raw_text, section_title, next_section_titles=None):
    if not raw_text:
        return None

    next_section_titles = next_section_titles or []

    start_pattern = re.escape(section_title)
    end_pattern = "|".join(re.escape(title) for title in next_section_titles) if next_section_titles else r"$"

    pattern = rf"{start_pattern}(.*?)(?:{end_pattern})"
    match = re.search(pattern, raw_text, flags=re.IGNORECASE | re.DOTALL)

    if not match:
        return None

    return normalize_text_field(match.group(1))


def get_value_after_label_from_text(section_text, label):
    if not section_text:
        return None

    lines = split_lines(section_text)
    return get_value_after_label(lines, label)


def apply_cross_task_inference(task_rows):
    if not task_rows or len(task_rows) < 2:
        return task_rows

    cloud_rows = [
        row for row in task_rows
        if row.get("label_main_team") == "iNET Cloud Support Team"
    ]

    if len(cloud_rows) < 2:
        return task_rows

    explicit_rows = [
        row for row in cloud_rows
        if row.get("label_sub_team") in ["AWS Team", "GCP Team"]
    ]

    both_rows = [
        row for row in cloud_rows
        if row.get("label_sub_team") == "GCP & AWS Team (Both)"
    ]

    if not both_rows:
        return task_rows

    explicit_teams = {row.get("label_sub_team") for row in explicit_rows}

    combined_env = " ".join([
        (row.get("related_env_raw") or row.get("related_env") or "").upper()
        for row in cloud_rows
    ])

    env_has_aws = "AWS" in combined_env
    env_has_gcp = "GCP" in combined_env or "GOOGLE" in combined_env

    if explicit_teams == {"GCP Team"} and env_has_aws and env_has_gcp:
        for row in both_rows:
            row["label_sub_team"] = "AWS Team"
            row["label_source"] = "cross_task_env_opposite_inference"
            row["cross_task_inference_used"] = True

    elif explicit_teams == {"AWS Team"} and env_has_aws and env_has_gcp:
        for row in both_rows:
            row["label_sub_team"] = "GCP Team"
            row["label_source"] = "cross_task_env_opposite_inference"
            row["cross_task_inference_used"] = True

    elif len(explicit_teams) == 1:
        only_team = list(explicit_teams)[0]
        for row in both_rows:
            row["label_sub_team"] = only_team
            row["label_source"] = "cross_task_same_inference"
            row["cross_task_inference_used"] = True

    return task_rows


# =========================================================
# 2) FIELD EXTRACTION (LINE-BASED)
# =========================================================
SECTION_HEADERS = {
    "request_details": "request details:",
    "requester_details": "requester details:",
    "service_request_details": "service request details:",
    "catalog_task_details": "catalog task details:",
    "incident_task_details": "incident task details:",
    "change_task_details": "change task details:",
    "alert_details": "alert details:",
    "recommendation": "recommendation:",
}


def split_lines(text):
    if not text:
        return []
    text = normalize_text_field(text)
    if not text:
        return []
    return [line.strip() for line in text.split("\n") if line.strip()]


def get_value_after_label(lines, label, start_idx=0, stop_labels=None):
    label_lower = label.lower()
    stop_labels = stop_labels or []

    for i in range(start_idx, len(lines)):
        line = lines[i]
        if line.lower().startswith(label_lower):
            after = line[len(label):].strip()
            if after:
                return after

            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue

                next_lower = next_line.lower()
                if any(next_lower.startswith(s.lower()) for s in stop_labels):
                    return None

                if re.match(r"^[A-Za-z][A-Za-z /()._-]*:\s*", next_line):
                    return None

                return next_line
    return None


def get_section_indices(lines):
    indices = {}
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for key, header in SECTION_HEADERS.items():
            if line_lower == header:
                indices[key] = i
    return indices


def extract_section_block(lines, start_key, next_keys):
    indices = get_section_indices(lines)
    start = indices.get(start_key)
    if start is None:
        return []

    end = len(lines)
    for nk in next_keys:
        idx = indices.get(nk)
        if idx is not None and idx > start:
            end = min(end, idx)

    return lines[start:end]


def extract_multiline_after_label(lines, label, stop_labels):
    label_lower = label.lower()
    for i, line in enumerate(lines):
        if line.lower().startswith(label_lower):
            first = line[len(label):].strip()
            collected = []
            if first:
                collected.append(first)

            j = i + 1
            while j < len(lines):
                current = lines[j].strip()
                current_lower = current.lower()

                if any(current_lower.startswith(s.lower()) for s in stop_labels):
                    break

                if current_lower in SECTION_HEADERS.values():
                    break

                collected.append(current)
                j += 1

            text = "\n".join([x for x in collected if x.strip()])
            return text if text else None
    return None


def extract_ticket_info(body, subject=""):
    lines = split_lines(body)
    subject_decoded = decode_mime_words(subject or "")

    request_block = extract_section_block(
        lines,
        "request_details",
        ["requester_details", "service_request_details", "catalog_task_details", "incident_task_details", "change_task_details"]
    )
    requester_block = extract_section_block(
        lines,
        "requester_details",
        ["service_request_details", "catalog_task_details", "incident_task_details", "change_task_details"]
    )
    service_request_block = extract_section_block(
        lines,
        "service_request_details",
        ["catalog_task_details", "incident_task_details", "change_task_details"]
    )
    catalog_task_block = extract_section_block(
        lines,
        "catalog_task_details",
        ["incident_task_details", "change_task_details"]
    )
    incident_task_block = extract_section_block(
        lines,
        "incident_task_details",
        ["change_task_details", "alert_details", "recommendation"]
    )
    change_task_block = extract_section_block(
        lines,
        "change_task_details",
        ["alert_details", "recommendation"]
    )

    catalog_task_text = extract_section_text(
        body,
        "Catalog Task Details:",
        ["Incident Task Details:", "Change Task Details:", "Alert Details:", "Recommendation:"]
    )

    service_request_text = extract_section_text(
        body,
        "Service Request Details:",
        ["Catalog Task Details:", "Incident Task Details:", "Change Task Details:"]
    )

    incident_task_text = extract_section_text(
        body,
        "Incident Task Details:",
        ["Change Task Details:", "Alert Details:", "Recommendation:"]
    )

    change_task_text = extract_section_text(
        body,
        "Change Task Details:",
        ["Alert Details:", "Recommendation:"]
    )

    results = {
        "request_number": get_value_after_label(request_block, "Request Number:"),
        "ritm_no": get_value_after_label(service_request_block, "Service Request Number:"),
        "task_no": get_value_after_label(catalog_task_block, "Task Number:"),
        "inc_no": None,
        "itask_no": get_value_after_label(incident_task_block, "Number:"),
        "ctask_no": get_value_after_label(change_task_block, "Number:"),
        "opened_by": get_value_after_label(request_block, "Opened By:"),
        "requested_for": get_value_after_label(requester_block, "Requested For:"),
        "raised_by": get_value_after_label(incident_task_block, "Raised by:"),
        "business_service": get_value_after_label(incident_task_block, "Business Service:"),
        "service_offering": get_value_after_label(incident_task_block, "Service Offering:"),
        "priority": get_value_after_label(incident_task_block, "Priority:"),
        "urgency": get_value_after_label(incident_task_block, "Urgency:"),
        "impact": get_value_after_label(incident_task_block, "Impact:"),
        "email_address": (
            get_value_after_label(requester_block, "Email Address:")
            or get_value_after_label(incident_task_block, "Email Address:")
        ),
        "state": (
            get_value_after_label(catalog_task_block, "State:")
            or get_value_after_label(service_request_block, "State:")
        ),
        "task_short_desc": get_value_after_label(catalog_task_block, "Short Description:"),
        "ritm_short_desc": get_value_after_label(service_request_block, "Short Description:"),
        "inc_short_desc": get_value_after_label(incident_task_block, "Short Description:"),
        "ctask_short_desc": get_value_after_label(change_task_block, "Short Description:"),
        "related_env": extract_multiline_after_label(
            service_request_block,
            "Related environment:",
            stop_labels=["State:", "Task Number:", "Catalog Task Details:", "Click here", "Click Here"]
        ),
    }

    results["task_no"] = (
        results["task_no"]
        or get_value_after_label_from_text(catalog_task_text, "Task Number:")
        or extract_first_by_pattern(subject_decoded, r"\bTASK\d+\b")
        or extract_first_by_pattern(body, r"\bTASK\d+\b")
    )

    results["task_short_desc"] = (
        results["task_short_desc"]
        or get_value_after_label_from_text(catalog_task_text, "Short Description:")
        or extract_catalog_task_short_desc(body)
    )

    results["ritm_no"] = (
        results["ritm_no"]
        or get_value_after_label_from_text(service_request_text, "Service Request Number:")
        or extract_first_by_pattern(body, r"\bRITM\d+\b")
    )

    results["ritm_short_desc"] = (
        results["ritm_short_desc"]
        or get_value_after_label_from_text(service_request_text, "Short Description:")
    )

    results["itask_no"] = (
        results["itask_no"]
        or get_value_after_label_from_text(incident_task_text, "Number:")
        or extract_first_by_pattern(subject_decoded, r"\bITASK\d+\b")
        or extract_first_by_pattern(body, r"\bITASK\d+\b")
    )

    results["inc_short_desc"] = (
        results["inc_short_desc"]
        or get_value_after_label_from_text(incident_task_text, "Short Description:")
    )

    results["ctask_no"] = (
        results["ctask_no"]
        or get_value_after_label_from_text(change_task_text, "Number:")
        or extract_first_by_pattern(subject_decoded, r"\bCTASK\d+\b")
        or extract_first_by_pattern(body, r"\bCTASK\d+\b")
    )

    results["ctask_short_desc"] = (
        results["ctask_short_desc"]
        or get_value_after_label_from_text(change_task_text, "Short Description:")
    )

    results["description"] = (
        extract_multiline_after_label(
            service_request_block,
            "Description:",
            stop_labels=["State:", "Click here", "Catalog Task Details:", "Task Number:", "Related environment:"]
        )
        or extract_multiline_after_label(
            incident_task_block,
            "Description:",
            stop_labels=["Alert Details:", "Recommendation:", "Click here", "Number:", "Raised by:"]
        )
        or extract_multiline_after_label(
            change_task_block,
            "Description:",
            stop_labels=["Click here", "Number:", "Short Description:"]
        )
    )

    results["urls"] = find_urls(body)
    results["ips"] = find_ips(body)

    is_ritm_assign = (
        "Catalog Task Assignment" in subject_decoded
        or "A Catalog Task record has been assigned" in (body or "")
        or re.search(r"Catalog Task\s+TASK\d+\s+has been assigned", subject_decoded, re.IGNORECASE)
    )

    is_itask_assign = bool(
        "Incident Task Assignment" in subject_decoded
        or "A Incident Task record has been assigned" in (body or "")
        or re.search(r"\bITASK\d+\b", subject_decoded, re.IGNORECASE)
        or re.search(r"\bITASK\d+\b", body or "", re.IGNORECASE)
    )

    is_ctask_assign = bool(
        "Change task" in subject_decoded
        or "A Change Task record has been assigned" in (body or "")
        or re.search(r"\bCTASK\d+\b", subject_decoded, re.IGNORECASE)
        or re.search(r"\bCTASK\d+\b", body or "", re.IGNORECASE)
    )

    current_state = (results.get("state") or "").lower()
    is_assigned_state = ("assigned" in current_state) or (results.get("state") is None)

    results["is_valid_ritm"] = bool(is_ritm_assign and is_assigned_state)
    results["is_valid_itask"] = bool(is_itask_assign)
    results["is_valid_ctask"] = bool(is_ctask_assign)

    return results


def get_ticket_type(info):
    if info.get("is_valid_ritm"):
        return "catalog_task"
    if info.get("is_valid_itask"):
        return "incident_task"
    if info.get("is_valid_ctask"):
        return "change_task"
    return "unknown"


def identify_task_and_parent(info):
    current_task_id = None
    parent_id = None

    if info.get("is_valid_itask"):
        current_task_id = info.get("itask_no")
        parent_id = info.get("itask_no")
    elif info.get("is_valid_ritm"):
        current_task_id = info.get("task_no")
        parent_id = info.get("ritm_no") or info.get("task_no")
    elif info.get("is_valid_ctask"):
        current_task_id = info.get("ctask_no")
        parent_id = info.get("ctask_no")

    return current_task_id, parent_id


# =========================================================
# 3) CLEANING FOR WEB / MODEL
# =========================================================
NOISE_LINE_PATTERNS = [
    r"^\*\*\*\s*Please DO-NOT-REPLY.*",
    r"^Click here to view the request.*",
    r"^Click here to view the item.*",
    r"^Click here to view the task.*",
    r"^Click here to view the Incident Task record.*",
    r"^Click here to view the Change Task record.*",
    r"^A Catalog Task record has been assigned to your group$",
    r"^A Incident Task record has been assigned to your group$",
    r"^A Change Task record has been assigned to your group$",
    r"^Catalog Task Assignment Notification$",
    r"^Incident Task Assignment Notification$",
    r"^Change Task Assignment Notification$",
    r"^Request Details:$",
    r"^Requester Details:$",
    r"^Service Request Details:$",
    r"^Catalog Task Details:$",
    r"^Ref:MSG\d+.*$",
]


def remove_noise_lines(text):
    if not text:
        return None

    lines = split_lines(text)
    cleaned = []

    for line in lines:
        line = normalize_scalar(line)
        if not line:
            continue

        skip = False
        for pat in NOISE_LINE_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                skip = True
                break

        if skip:
            continue

        cleaned.append(line)

    return "\n".join(cleaned) if cleaned else None


def clean_body_for_training(text):
    text = remove_noise_lines(text)
    if not text:
        return None
    text = mask_ticket_ids(text)
    return normalize_text_field(text, max_len=Config.MAX_BODY_MODEL_LEN)


def summarize_for_web(text, max_len=1500):
    text = remove_noise_lines(text)
    return normalize_text_field(text, max_len=max_len)


# =========================================================
# 4) ROUTING LOGIC
# =========================================================
def detect_assigned_team_by_to(to_address):
    to_address = (to_address or "").lower()
    for email_addr, team_name in Config.TARGET_RECEIVER.items():
        if email_addr.lower() in to_address:
            return team_name
    return None


def build_feature_flags(info, clean_body, subject=""):
    full_content = (clean_body or "").upper()
    related_env = (info.get("related_env") or "").upper()
    task_short_desc = (info.get("task_short_desc") or "").upper()
    ritm_short_desc = (info.get("ritm_short_desc") or "").upper()
    inc_short_desc = (info.get("inc_short_desc") or "").upper()
    ctask_short_desc = (info.get("ctask_short_desc") or "").upper()
    description = (info.get("description") or "").upper()
    subject_upper = (subject or "").upper()

    has_aws_ip = any(ip.startswith("10.41.") for ip in info.get("ips", []))
    has_gcp_ip = any(ip.startswith("10.42.") for ip in info.get("ips", []))

    combined_headers = f"{subject_upper} {task_short_desc} {ritm_short_desc} {inc_short_desc} {ctask_short_desc}"
    header_plus_desc = f"{combined_headers} {description}"

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
    full_content = (clean_body or "").upper()
    env_text = (info.get("related_env") or "").upper()
    task_header = (info.get("task_short_desc") or "").upper()
    ritm_header = (info.get("ritm_short_desc") or "").upper()
    inc_header = (info.get("inc_short_desc") or "").upper()
    ctask_header = (info.get("ctask_short_desc") or "").upper()
    desc_text = (info.get("description") or "").upper()
    subject_text = (subject or "").upper()

    flags = build_feature_flags(info, clean_body, subject)

    gcp_keywords = list(Config.GCP_KEYWORDS) + [
        "GEMINI", "CLOUDFUNCTIONS", "CLOUD RUN", "SPOKE01", "SHAREDSERVICES-PRD-RG"
    ]
    aws_keywords = list(Config.AWS_KEYWORDS) + [
        "PHASSAKORN SEENIL"
    ]

    explicit_task_text = f"{task_header}"
    explicit_ritm_text = f"{ritm_header}"
    explicit_subject_text = f"{subject_text}"

    if "[AWS]" in explicit_task_text and "[GCP]" not in explicit_task_text:
        return "AWS Team", "task_short_desc_prefix", flags
    if "[GCP]" in explicit_task_text and "[AWS]" not in explicit_task_text:
        return "GCP Team", "task_short_desc_prefix", flags

    if "[AWS]" in explicit_ritm_text and "[GCP]" not in explicit_ritm_text:
        return "AWS Team", "ritm_short_desc_prefix", flags
    if "[GCP]" in explicit_ritm_text and "[AWS]" not in explicit_ritm_text:
        return "GCP Team", "ritm_short_desc_prefix", flags

    if "[AWS]" in explicit_subject_text and "[GCP]" not in explicit_subject_text:
        return "AWS Team", "subject_prefix", flags
    if "[GCP]" in explicit_subject_text and "[AWS]" not in explicit_subject_text:
        return "GCP Team", "subject_prefix", flags

    task_hub = detect_hub_from_text(task_header)
    if task_hub:
        return task_hub, "task_short_desc_hub", flags

    if info.get("ips"):
        if any(ip.startswith("10.41.") for ip in info["ips"]):
            return "AWS Team", "ip_match", flags
        if any(ip.startswith("10.42.") for ip in info["ips"]):
            return "GCP Team", "ip_match", flags

    combined_headers = f"{task_header} {ritm_header} {inc_header} {ctask_header}"

    is_header_gcp = contains_any_loose(combined_headers, gcp_keywords)
    is_header_aws = contains_any_loose(combined_headers, aws_keywords)

    if is_header_gcp and not is_header_aws:
        return "GCP Team", "keyword_header", flags
    if is_header_aws and not is_header_gcp:
        return "AWS Team", "keyword_header", flags

    desc_has_gcp = contains_any_loose(full_content, ["GOOGLE", "GCP", "GEMINI", "GOOGLE WORKSPACE"])
    desc_has_aws = contains_any_loose(full_content, ["AWS", "AMAZON", "AWS HUB"])

    if (env_text.count("GCP") > 0 or desc_has_gcp) and not desc_has_aws:
        return "GCP Team", "keyword_body_env", flags
    if (env_text.count("AWS") > 0 or desc_has_aws) and not desc_has_gcp:
        return "AWS Team", "keyword_body_env", flags

    header_content = f"{subject_text} {ritm_header} {desc_text}"

    is_content_gcp = contains_any_loose(header_content, gcp_keywords)
    is_content_aws = contains_any_loose(header_content, aws_keywords)

    if is_content_gcp and not is_content_aws:
        return "GCP Team", "keyword_desc", flags
    if is_content_aws and not is_content_gcp:
        return "AWS Team", "keyword_desc", flags

    for url in info.get("urls", []):
        url_lower = url.lower()
        for domain, team in Config.SYSTEM_MAPPING.items():
            if domain.lower() in url_lower:
                return team, "url_match", flags

    return "GCP & AWS Team (Both)", "fallback_both", flags


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


# =========================================================
# 6) HEADERS
# =========================================================
MASTER_DB_HEADERS = [
    "record_id", "parent_id", "message_id", "email_date",
    "from_address", "to_address", "ticket_type",
    "request_number", "ritm_no", "inc_no", "itask_no", "ctask_no",
    "subject_clean", "short_desc_clean", "description_clean",
    "description_for_model", "related_env_raw", "body_for_model",
    "opened_by", "requested_for", "raised_by",
    "business_service", "service_offering", "priority", "urgency", "impact", "contact_email",
    "ip_list_json", "url_list_json",
    "has_aws_ip", "has_gcp_ip",
    "has_aws_keyword_header", "has_gcp_keyword_header",
    "has_aws_keyword_body", "has_gcp_keyword_body",
    "has_aws_keyword_desc", "has_gcp_keyword_desc",
    "env_has_aws", "env_has_gcp",
    "assigned_group_from_to", "route_scope",
    "sibling_task_count", "sibling_known_sub_team", "cross_task_inference_used",
    "label_main_team", "label_sub_team", "label_source", "text_input"
]

AUDIT_RAW_HEADERS = [
    "record_id", "parent_id", "message_id", "email_date",
    "subject_raw", "body_raw",
    "parsed_task_short_desc", "parsed_ritm_short_desc", "parsed_inc_short_desc", "parsed_ctask_short_desc",
    "parsed_description", "parsed_related_env", "parsed_requested_for", "parsed_opened_by",
    "parsed_business_service", "parsed_service_offering",
    "ip_list_json", "url_list_json"
]

TRAINING_HEADERS = [
    "record_id", "ticket_type", "to_address", "subject_clean", "short_desc_clean",
    "description_for_model", "related_env_raw", "body_for_model", "text_input",
    "label_main_team", "label_sub_team"
]

TRAINING_MAIN_TEAM_HEADERS = [
    "record_id", "ticket_type", "to_address", "subject_clean", "short_desc_clean",
    "related_env_raw", "text_input", "label_main_team"
]

TRAINING_CLOUD_SUBTEAM_HEADERS = [
    "record_id", "ticket_type", "to_address", "subject_clean", "short_desc_clean",
    "description_for_model", "related_env_raw", "body_for_model", "text_input", "label_sub_team"
]


# =========================================================
# 7) CSV
# =========================================================
def sanitize_row_for_csv(row, headers):
    result = {}
    for h in headers:
        v = row.get(h)
        if isinstance(v, bool):
            result[h] = "true" if v else "false"
        elif v is None:
            result[h] = ""
        else:
            result[h] = v
    return result


def write_csv(filename, headers, rows):
    if not rows:
        print(f"ℹ️ No rows to write for {filename}")
        return

    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(sanitize_row_for_csv(row, headers))

    print(f"✅ Exported {len(rows)} rows to {filename}")


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