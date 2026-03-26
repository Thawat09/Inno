import os
import re
import pandas as pd

from datetime import datetime


# =========================================================
# 2) UTILS
# =========================================================
def get_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col in df.columns:
        return df[col].fillna("").astype(str)
    return pd.Series([""] * len(df), index=df.index, dtype="object")


def get_versioned_model_path(base_name: str, target_model_path: str, extension: str = ".pkl") -> str:
    model_dir = os.path.dirname(target_model_path)
    year_th = (datetime.now().year + 543) % 100
    date_str = datetime.now().strftime(f"{year_th}_%m_%d")
    version = 1

    while True:
        file_name = f"{base_name}_{date_str}_v{version}{extension}"
        full_path = os.path.join(model_dir, file_name)
        if not os.path.exists(full_path):
            return full_path
        version += 1


def safe_text(value) -> str:
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()


def normalize_for_logic(text: str) -> str:
    text = safe_text(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()


def count_keyword_hits(text: str, keywords: list) -> int:
    if not text:
        return 0
    text_upper = text.upper()
    return sum(1 for k in keywords if str(k).upper() in text_upper)