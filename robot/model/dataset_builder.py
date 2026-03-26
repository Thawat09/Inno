import os
import pandas as pd

from typing import Set

from model.train_helpers import get_series
from model.rule_engine import (
    build_logic_features,
    detect_rule_label,
)


# =========================================================
# 3) DATA PREP
# =========================================================
def build_text_input(df: pd.DataFrame) -> pd.Series:
    return (
        "TICKET_TYPE: " + get_series(df, "ticket_type") + " ||| " +
        "TO_ADDRESS: " + get_series(df, "to_address") + " ||| " +
        "SUBJECT: " + get_series(df, "subject_clean") + " ||| " +
        "SHORT_DESC: " + get_series(df, "short_desc_clean") + " ||| " +
        "DETAIL: " + get_series(df, "description_for_model") + " ||| " +
        "ENV: " + get_series(df, "related_env_raw") + " ||| " +
        "BODY: " + get_series(df, "body_for_model")
    )


def load_dataset(
    dataset_path: str,
    target_column: str,
    valid_labels: Set[str],
    enable_rules: bool = True
):
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ dataset: {dataset_path}")

    df = pd.read_csv(dataset_path)

    if target_column not in df.columns:
        raise ValueError(
            f"ไม่พบคอลัมน์ target '{target_column}' ในไฟล์ {dataset_path}\n"
            f"columns ที่มี: {list(df.columns)}"
        )

    df = df.dropna(subset=[target_column]).copy()
    df[target_column] = df[target_column].astype(str).str.strip()
    df = df[df[target_column].isin(valid_labels)].copy()

    if df.empty:
        raise ValueError(
            f"ไม่มีข้อมูลหลัง filter valid labels สำหรับ target '{target_column}'. "
            f"valid_labels={sorted(valid_labels)}"
        )

    if "text_input" not in df.columns:
        df["text_input"] = build_text_input(df)

    df["text_input"] = df["text_input"].fillna("").astype(str).str.strip()
    df = df[df["text_input"] != ""].copy()

    if df.empty:
        raise ValueError("ไม่มีข้อมูลหลังจากตัดแถวที่ text_input ว่าง")

    df = build_logic_features(df)

    if enable_rules:
        rule_outputs = df.apply(lambda row: detect_rule_label(row, valid_labels), axis=1)
        df["rule_label"] = [x[0] for x in rule_outputs]
        df["rule_source"] = [x[1] for x in rule_outputs]
    else:
        df["rule_label"] = None
        df["rule_source"] = None

    df["combined_features"] = (
        df["text_input"].fillna("").astype(str) + " ||| " +
        df["logic_text"].fillna("").astype(str)
    )

    df["explain_text_features"] = (
        "TICKET_TYPE: " + get_series(df, "ticket_type") + " ||| " +
        "TO_ADDRESS: " + get_series(df, "to_address") + " ||| " +
        "SUBJECT: " + get_series(df, "subject_clean") + " ||| " +
        "SHORT_DESC: " + get_series(df, "short_desc_clean") + " ||| " +
        "DETAIL: " + get_series(df, "description_for_model") + " ||| " +
        "ENV: " + get_series(df, "related_env_raw") + " ||| " +
        "BODY: " + get_series(df, "body_for_model")
    )

    X = df["combined_features"]
    y = df[target_column]

    return df, X, y