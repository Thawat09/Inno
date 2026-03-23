import re
from app.config import Config
from app.utils.extract_utils import split_lines
from app.utils.text_utils import mask_ticket_ids, normalize_scalar, normalize_text_field


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


# =========================================================
# 3) CLEANING FOR WEB / MODEL
# =========================================================
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
