from app.config import Config
from app.utils.text_utils import contains_any, contains_any_loose, detect_hub_from_text, normalize_scalar


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
