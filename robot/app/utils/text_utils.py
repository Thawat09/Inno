import json
import re
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
