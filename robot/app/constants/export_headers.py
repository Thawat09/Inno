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
