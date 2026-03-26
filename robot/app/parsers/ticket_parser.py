import re
from app.utils.extract_utils import (
    extract_catalog_task_short_desc,
    extract_multiline_after_label,
    extract_section_block,
    extract_section_text,
    find_ips,
    find_urls,
    get_value_after_label,
    get_value_after_label_from_text,
    split_lines,
)
from app.utils.text_utils import decode_mime_words, extract_first_by_pattern


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


def extract_ticket_info(body, subject=""):
    lines = split_lines(body)
    subject_decoded = decode_mime_words(subject or "")

    request_block = extract_section_block(
        lines,
        "request_details",
        ["requester_details", "service_request_details", "catalog_task_details", "incident_task_details", "change_task_details"],
        SECTION_HEADERS
    )
    requester_block = extract_section_block(
        lines,
        "requester_details",
        ["service_request_details", "catalog_task_details", "incident_task_details", "change_task_details"],
        SECTION_HEADERS
    )
    service_request_block = extract_section_block(
        lines,
        "service_request_details",
        ["catalog_task_details", "incident_task_details", "change_task_details"],
        SECTION_HEADERS
    )
    catalog_task_block = extract_section_block(
        lines,
        "catalog_task_details",
        ["incident_task_details", "change_task_details"],
        SECTION_HEADERS
    )
    incident_task_block = extract_section_block(
        lines,
        "incident_task_details",
        ["change_task_details", "alert_details", "recommendation"],
        SECTION_HEADERS
    )
    change_task_block = extract_section_block(
        lines,
        "change_task_details",
        ["alert_details", "recommendation"],
        SECTION_HEADERS
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
            stop_labels=["State:", "Task Number:", "Catalog Task Details:", "Click here", "Click Here"],
            section_headers=SECTION_HEADERS
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
            stop_labels=["State:", "Click here", "Catalog Task Details:", "Task Number:", "Related environment:"],
            section_headers=SECTION_HEADERS
        )
        or extract_multiline_after_label(
            incident_task_block,
            "Description:",
            stop_labels=["Alert Details:", "Recommendation:", "Click here", "Number:", "Raised by:"],
            section_headers=SECTION_HEADERS
        )
        or extract_multiline_after_label(
            change_task_block,
            "Description:",
            stop_labels=["Click here", "Number:", "Short Description:"],
            section_headers=SECTION_HEADERS
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
