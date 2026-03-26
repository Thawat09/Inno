import ipaddress
import re
from app.utils.text_utils import (
    clean_html_to_text,
    decode_mime_words,
    normalize_scalar,
    normalize_text_field,
    normalize_text_single_line,
)


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


def get_section_indices(lines, section_headers):
    indices = {}
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for key, header in section_headers.items():
            if line_lower == header:
                indices[key] = i
    return indices


def extract_section_block(lines, start_key, next_keys, section_headers):
    indices = get_section_indices(lines, section_headers)
    start = indices.get(start_key)
    if start is None:
        return []

    end = len(lines)
    for nk in next_keys:
        idx = indices.get(nk)
        if idx is not None and idx > start:
            end = min(end, idx)

    return lines[start:end]


def extract_multiline_after_label(lines, label, stop_labels, section_headers):
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

                if current_lower in section_headers.values():
                    break

                collected.append(current)
                j += 1

            text = "\n".join([x for x in collected if x.strip()])
            return text if text else None
    return None


def get_value_after_label_from_text(section_text, label):
    if not section_text:
        return None

    lines = split_lines(section_text)
    return get_value_after_label(lines, label)
