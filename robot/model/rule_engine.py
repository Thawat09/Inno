import numpy as np
import pandas as pd

from typing import Dict, List, Optional, Tuple, Set

from model.train_settings import (
    CONFIDENCE_THRESHOLD,
    AWS_KEYWORDS,
    GCP_KEYWORDS,
    SYSTEM_MAPPING,
)
from model.train_helpers import (
    get_series,
    safe_text,
    normalize_for_logic,
    count_keyword_hits,
)


def detect_system_mapping_label(text: str, valid_labels: Set[str]) -> Tuple[Optional[str], Optional[str]]:
    norm_text = normalize_for_logic(text)
    if not norm_text:
        return None, None

    for domain, team in SYSTEM_MAPPING.items():
        if str(domain).upper() in norm_text and team in valid_labels:
            return team, f"rule_system_mapping:{domain}"

    return None, None


def detect_rule_label(row: pd.Series, valid_labels: Set[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Rule นี้ออกแบบมาสำหรับ cloud subteam เป็นหลัก
    จะคืนได้แค่ AWS Team / GCP Team ถ้าค่านั้นอยู่ใน valid_labels
    """
    subject = normalize_for_logic(row.get("subject_clean"))
    short_desc = normalize_for_logic(row.get("short_desc_clean"))
    related_env = normalize_for_logic(row.get("related_env_raw"))
    description = normalize_for_logic(row.get("description_for_model"))
    body = normalize_for_logic(row.get("body_for_model"))
    text_input = normalize_for_logic(row.get("text_input"))

    merged = " || ".join([subject, short_desc, related_env, description, body, text_input])

    if "AWS Team" in valid_labels:
        if "FIREWALL REQUEST : AWS HUB" in short_desc:
            return "AWS Team", "rule_task_short_desc_aws_hub"
        if "[AWS]" in merged:
            return "AWS Team", "rule_prefix_aws"
        if "10.41." in merged and "10.42." not in merged:
            return "AWS Team", "rule_ip_aws"

    if "GCP Team" in valid_labels:
        if "FIREWALL REQUEST : GCP HUB" in short_desc:
            return "GCP Team", "rule_task_short_desc_gcp_hub"
        if "[GCP]" in merged:
            return "GCP Team", "rule_prefix_gcp"
        if "10.42." in merged and "10.41." not in merged:
            return "GCP Team", "rule_ip_gcp"

    system_label, system_source = detect_system_mapping_label(merged, valid_labels)
    if system_label:
        return system_label, system_source

    header_text = " || ".join([subject, short_desc])
    gcp_header_hits = count_keyword_hits(header_text, GCP_KEYWORDS)
    aws_header_hits = count_keyword_hits(header_text, AWS_KEYWORDS)

    if "GCP Team" in valid_labels and gcp_header_hits > 0 and aws_header_hits == 0:
        return "GCP Team", "rule_header_keywords"
    if "AWS Team" in valid_labels and aws_header_hits > 0 and gcp_header_hits == 0:
        return "AWS Team", "rule_header_keywords"

    gcp_body_hits = count_keyword_hits(merged, GCP_KEYWORDS)
    aws_body_hits = count_keyword_hits(merged, AWS_KEYWORDS)

    if "GCP Team" in valid_labels and gcp_body_hits > 0 and aws_body_hits == 0:
        return "GCP Team", "rule_body_keywords"
    if "AWS Team" in valid_labels and aws_body_hits > 0 and gcp_body_hits == 0:
        return "AWS Team", "rule_body_keywords"

    return None, None


def build_logic_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["subject_clean"] = get_series(out, "subject_clean")
    out["short_desc_clean"] = get_series(out, "short_desc_clean")
    out["related_env_raw"] = get_series(out, "related_env_raw")
    out["description_for_model"] = get_series(out, "description_for_model")
    out["body_for_model"] = get_series(out, "body_for_model")
    out["ticket_type"] = get_series(out, "ticket_type")
    out["to_address"] = get_series(out, "to_address")

    merged_header = (
        out["subject_clean"] + " || " +
        out["short_desc_clean"]
    )

    merged_body = (
        out["related_env_raw"] + " || " +
        out["description_for_model"] + " || " +
        out["body_for_model"]
    )

    out["rule_has_gcp_hub"] = out["short_desc_clean"].str.upper().str.contains("GCP HUB", regex=False).astype(int)
    out["rule_has_aws_hub"] = out["short_desc_clean"].str.upper().str.contains("AWS HUB", regex=False).astype(int)

    out["rule_has_gcp_prefix"] = (
        merged_header.str.upper().str.contains(r"\[GCP\]", regex=True)
    ).astype(int)
    out["rule_has_aws_prefix"] = (
        merged_header.str.upper().str.contains(r"\[AWS\]", regex=True)
    ).astype(int)

    out["rule_has_gcp_ip"] = merged_body.str.contains("10.42.", regex=False).astype(int)
    out["rule_has_aws_ip"] = merged_body.str.contains("10.41.", regex=False).astype(int)

    out["gcp_kw_header_hits"] = merged_header.apply(lambda x: count_keyword_hits(x, GCP_KEYWORDS))
    out["aws_kw_header_hits"] = merged_header.apply(lambda x: count_keyword_hits(x, AWS_KEYWORDS))
    out["gcp_kw_body_hits"] = merged_body.apply(lambda x: count_keyword_hits(x, GCP_KEYWORDS))
    out["aws_kw_body_hits"] = merged_body.apply(lambda x: count_keyword_hits(x, AWS_KEYWORDS))

    out["logic_text"] = (
        "TICKET_TYPE=" + out["ticket_type"] + " || " +
        "TO=" + out["to_address"] + " || " +
        "SUBJECT=" + out["subject_clean"] + " || " +
        "SHORT_DESC=" + out["short_desc_clean"] + " || " +
        "ENV=" + out["related_env_raw"] + " || " +
        "DESC=" + out["description_for_model"] + " || " +
        "BODY=" + out["body_for_model"] + " || " +
        "RULE_GCP_HUB=" + out["rule_has_gcp_hub"].astype(str) + " || " +
        "RULE_AWS_HUB=" + out["rule_has_aws_hub"].astype(str) + " || " +
        "RULE_GCP_IP=" + out["rule_has_gcp_ip"].astype(str) + " || " +
        "RULE_AWS_IP=" + out["rule_has_aws_ip"].astype(str) + " || " +
        "GCP_HEADER_HITS=" + out["gcp_kw_header_hits"].astype(str) + " || " +
        "AWS_HEADER_HITS=" + out["aws_kw_header_hits"].astype(str) + " || " +
        "GCP_BODY_HITS=" + out["gcp_kw_body_hits"].astype(str) + " || " +
        "AWS_BODY_HITS=" + out["aws_kw_body_hits"].astype(str)
    )

    return out


def rebuild_text_input_for_row(row_dict: Dict) -> str:
    return (
        "TICKET_TYPE: " + safe_text(row_dict.get("ticket_type")) + " ||| " +
        "TO_ADDRESS: " + safe_text(row_dict.get("to_address")) + " ||| " +
        "SUBJECT: " + safe_text(row_dict.get("subject_clean")) + " ||| " +
        "SHORT_DESC: " + safe_text(row_dict.get("short_desc_clean")) + " ||| " +
        "DETAIL: " + safe_text(row_dict.get("description_for_model")) + " ||| " +
        "ENV: " + safe_text(row_dict.get("related_env_raw")) + " ||| " +
        "BODY: " + safe_text(row_dict.get("body_for_model"))
    )


def score_row_for_team(row_dict: Dict, team_name: str) -> int:
    text = normalize_for_logic(
        " || ".join([
            safe_text(row_dict.get("subject_clean")),
            safe_text(row_dict.get("short_desc_clean")),
            safe_text(row_dict.get("description_for_model")),
            safe_text(row_dict.get("related_env_raw")),
            safe_text(row_dict.get("body_for_model")),
            safe_text(row_dict.get("text_input")),
        ])
    )

    if team_name == "AWS Team":
        return count_keyword_hits(text, AWS_KEYWORDS)
    if team_name == "GCP Team":
        return count_keyword_hits(text, GCP_KEYWORDS)
    return 0


def resolve_two_task_case(records: List[Dict], bundle):
    from model.training_engine import predict_with_rules_first

    outputs = []
    temp = []

    for row in records:
        pred = predict_with_rules_first(row, bundle)
        temp.append({
            "row": row,
            "pred": pred
        })

    catalog_rows = [x for x in temp if safe_text(x["row"].get("ticket_type")) == "catalog_task"]

    if len(catalog_rows) == 2:
        row1, row2 = catalog_rows[0], catalog_rows[1]

        pred1 = row1["pred"]["predicted_label"]
        pred2 = row2["pred"]["predicted_label"]

        used_rule1 = row1["pred"].get("used_rule", False)
        used_rule2 = row2["pred"].get("used_rule", False)

        conf1 = row1["pred"].get("confidence", 0.0)
        conf2 = row2["pred"].get("confidence", 0.0)

        row1_aws_score = score_row_for_team(row1["row"], "AWS Team")
        row1_gcp_score = score_row_for_team(row1["row"], "GCP Team")
        row2_aws_score = score_row_for_team(row2["row"], "AWS Team")
        row2_gcp_score = score_row_for_team(row2["row"], "GCP Team")

        if used_rule1 and not used_rule2:
            row2["pred"]["predicted_label"] = "AWS Team" if pred1 == "GCP Team" else "GCP Team"
            row2["pred"]["prediction_source"] = "two_task_opposite_inference_from_rule"

        elif used_rule2 and not used_rule1:
            row1["pred"]["predicted_label"] = "AWS Team" if pred2 == "GCP Team" else "GCP Team"
            row1["pred"]["prediction_source"] = "two_task_opposite_inference_from_rule"

        elif used_rule1 and used_rule2 and pred1 == pred2:
            if pred1 == "AWS Team":
                if row1_aws_score <= row2_aws_score:
                    row1["pred"]["predicted_label"] = "GCP Team"
                    row1["pred"]["prediction_source"] = "two_task_rule_conflict_flip"
                else:
                    row2["pred"]["predicted_label"] = "GCP Team"
                    row2["pred"]["prediction_source"] = "two_task_rule_conflict_flip"
            elif pred1 == "GCP Team":
                if row1_gcp_score <= row2_gcp_score:
                    row1["pred"]["predicted_label"] = "AWS Team"
                    row1["pred"]["prediction_source"] = "two_task_rule_conflict_flip"
                else:
                    row2["pred"]["predicted_label"] = "AWS Team"
                    row2["pred"]["prediction_source"] = "two_task_rule_conflict_flip"

        elif not used_rule1 and not used_rule2 and pred1 == pred2:
            if pred1 == "AWS Team":
                aws_gap1 = row1_aws_score - row1_gcp_score
                aws_gap2 = row2_aws_score - row2_gcp_score
                if aws_gap1 < aws_gap2:
                    row1["pred"]["predicted_label"] = "GCP Team"
                    row1["pred"]["prediction_source"] = "two_task_keyword_gap_flip"
                elif aws_gap2 < aws_gap1:
                    row2["pred"]["predicted_label"] = "GCP Team"
                    row2["pred"]["prediction_source"] = "two_task_keyword_gap_flip"
                else:
                    if conf1 <= conf2:
                        row1["pred"]["predicted_label"] = "GCP Team"
                        row1["pred"]["prediction_source"] = "two_task_confidence_flip"
                    else:
                        row2["pred"]["predicted_label"] = "GCP Team"
                        row2["pred"]["prediction_source"] = "two_task_confidence_flip"

            elif pred1 == "GCP Team":
                gcp_gap1 = row1_gcp_score - row1_aws_score
                gcp_gap2 = row2_gcp_score - row2_aws_score
                if gcp_gap1 < gcp_gap2:
                    row1["pred"]["predicted_label"] = "AWS Team"
                    row1["pred"]["prediction_source"] = "two_task_keyword_gap_flip"
                elif gcp_gap2 < gcp_gap1:
                    row2["pred"]["predicted_label"] = "AWS Team"
                    row2["pred"]["prediction_source"] = "two_task_keyword_gap_flip"
                else:
                    if conf1 <= conf2:
                        row1["pred"]["predicted_label"] = "AWS Team"
                        row1["pred"]["prediction_source"] = "two_task_confidence_flip"
                    else:
                        row2["pred"]["predicted_label"] = "AWS Team"
                        row2["pred"]["prediction_source"] = "two_task_confidence_flip"

        elif not used_rule1 and not used_rule2:
            if conf1 < CONFIDENCE_THRESHOLD <= conf2:
                row1["pred"]["predicted_label"] = "AWS Team" if pred2 == "GCP Team" else "GCP Team"
                row1["pred"]["prediction_source"] = "two_task_low_confidence_opposite"
            elif conf2 < CONFIDENCE_THRESHOLD <= conf1:
                row2["pred"]["predicted_label"] = "AWS Team" if pred1 == "GCP Team" else "GCP Team"
                row2["pred"]["prediction_source"] = "two_task_low_confidence_opposite"

    for x in temp:
        outputs.append({
            **x["row"],
            "predicted_label": x["pred"]["predicted_label"],
            "prediction_source": x["pred"]["prediction_source"],
            "confidence": x["pred"].get("confidence"),
            "is_low_confidence": x["pred"].get("is_low_confidence", False)
        })

    return outputs