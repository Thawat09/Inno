import os
import re
import sys
import json
import joblib
import numpy as np
import pandas as pd

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression, SGDClassifier, RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB, ComplementNB, BernoulliNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.config import Config
from app.utils.ml_utils import thai_tokenizer


# =========================================================
# 1) CONFIG
# =========================================================
DATASET_PATH = Config.TRAINING_CLOUD_SUBTEAM_DATASET_PATH
print(f"🔧 Configured dataset path: {DATASET_PATH}")
TARGET_COLUMN = Config.TRAINING_TARGET_COLUMN_CLOUD_SUBTEAM
MODEL_OUTPUT_PATH = Config.BEST_TICKET_CLASSIFIER_MODEL_PATH
ENSEMBLE_OUTPUT_PATH = Config.ENSEMBLE_BUNDLE_PATH
REPORT_OUTPUT_PATH = Config.MODEL_COMPARISON_REPORT_PATH
FEATURE_IMPORTANCE_OUTPUT_PATH = Config.FEATURE_IMPORTANCE_OUTPUT_PATH
EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH = Config.EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH

TEST_SIZE = Config.ML_TEST_SIZE
RANDOM_STATE = Config.ML_RANDOM_STATE
CONFIDENCE_THRESHOLD = Config.ML_CONFIDENCE_THRESHOLD

VALID_LABELS = {
    x.strip()
    for x in Config.VALID_CLOUD_SUBTEAM_LABELS.split(",")
    if x.strip()
}


# =========================================================
# 2) RULE CONFIG
# =========================================================
AWS_KEYWORDS = list(Config.AWS_KEYWORDS) + list(Config.EXTRA_AWS_KEYWORDS)
GCP_KEYWORDS = list(Config.GCP_KEYWORDS) + list(Config.EXTRA_GCP_KEYWORDS)
SYSTEM_MAPPING = getattr(Config, "SYSTEM_MAPPING", {})


# =========================================================
# 3) UTILS
# =========================================================
def safe_text(value) -> str:
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()


def contains_any_loose(text: str, keywords: List[str]) -> bool:
    if not text:
        return False
    text_upper = text.upper()
    return any(str(k).upper() in text_upper for k in keywords)


def normalize_for_logic(text: str) -> str:
    text = safe_text(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()


def count_keyword_hits(text: str, keywords: List[str]) -> int:
    if not text:
        return 0
    text_upper = text.upper()
    return sum(1 for k in keywords if str(k).upper() in text_upper)


def detect_system_mapping_label(text: str) -> Tuple[Optional[str], Optional[str]]:
    norm_text = normalize_for_logic(text)
    if not norm_text:
        return None, None

    for domain, team in SYSTEM_MAPPING.items():
        if str(domain).upper() in norm_text:
            return team, f"rule_system_mapping:{domain}"

    return None, None


def detect_rule_label(row: pd.Series) -> Tuple[Optional[str], Optional[str]]:
    subject = normalize_for_logic(row.get("subject_clean"))
    short_desc = normalize_for_logic(row.get("short_desc_clean"))
    related_env = normalize_for_logic(row.get("related_env_raw"))
    description = normalize_for_logic(row.get("description_for_model"))
    body = normalize_for_logic(row.get("body_for_model"))
    text_input = normalize_for_logic(row.get("text_input"))

    merged = " || ".join([subject, short_desc, related_env, description, body, text_input])

    # 1) strongest explicit rules
    if "FIREWALL REQUEST : GCP HUB" in short_desc:
        return "GCP Team", "rule_task_short_desc_gcp_hub"
    if "FIREWALL REQUEST : AWS HUB" in short_desc:
        return "AWS Team", "rule_task_short_desc_aws_hub"

    if "[GCP]" in merged:
        return "GCP Team", "rule_prefix_gcp"
    if "[AWS]" in merged:
        return "AWS Team", "rule_prefix_aws"

    system_label, system_source = detect_system_mapping_label(merged)
    if system_label in VALID_LABELS:
        return system_label, system_source

    # 2) IP signals
    if "10.42." in merged and "10.41." not in merged:
        return "GCP Team", "rule_ip_gcp"
    if "10.41." in merged and "10.42." not in merged:
        return "AWS Team", "rule_ip_aws"

    # 3) keyword dominance in short_desc/subject first
    header_text = " || ".join([subject, short_desc])
    gcp_header_hits = count_keyword_hits(header_text, GCP_KEYWORDS)
    aws_header_hits = count_keyword_hits(header_text, AWS_KEYWORDS)

    if gcp_header_hits > 0 and aws_header_hits == 0:
        return "GCP Team", "rule_header_keywords"
    if aws_header_hits > 0 and gcp_header_hits == 0:
        return "AWS Team", "rule_header_keywords"

    # 4) body/env dominance
    gcp_body_hits = count_keyword_hits(merged, GCP_KEYWORDS)
    aws_body_hits = count_keyword_hits(merged, AWS_KEYWORDS)

    if gcp_body_hits > 0 and aws_body_hits == 0:
        return "GCP Team", "rule_body_keywords"
    if aws_body_hits > 0 and gcp_body_hits == 0:
        return "AWS Team", "rule_body_keywords"

    return None, None


def build_logic_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["subject_clean"] = out.get("subject_clean", "").fillna("").astype(str)
    out["short_desc_clean"] = out.get("short_desc_clean", "").fillna("").astype(str)
    out["related_env_raw"] = out.get("related_env_raw", "").fillna("").astype(str)
    out["description_for_model"] = out.get("description_for_model", "").fillna("").astype(str)
    out["body_for_model"] = out.get("body_for_model", "").fillna("").astype(str)
    out["ticket_type"] = out.get("ticket_type", "").fillna("").astype(str)
    out["to_address"] = out.get("to_address", "").fillna("").astype(str)

    merged_header = (
        out["subject_clean"].astype(str) + " || " +
        out["short_desc_clean"].astype(str)
    )

    merged_body = (
        out["related_env_raw"].astype(str) + " || " +
        out["description_for_model"].astype(str) + " || " +
        out["body_for_model"].astype(str)
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


# =========================================================
# 4) DATA PREP
# =========================================================
def build_text_input(df: pd.DataFrame) -> pd.Series:
    return (
        "TICKET_TYPE: " + df.get("ticket_type", "").fillna("").astype(str) + " ||| " +
        "TO_ADDRESS: " + df.get("to_address", "").fillna("").astype(str) + " ||| " +
        "SUBJECT: " + df.get("subject_clean", "").fillna("").astype(str) + " ||| " +
        "SHORT_DESC: " + df.get("short_desc_clean", "").fillna("").astype(str) + " ||| " +
        "DETAIL: " + df.get("description_for_model", "").fillna("").astype(str) + " ||| " +
        "ENV: " + df.get("related_env_raw", "").fillna("").astype(str) + " ||| " +
        "BODY: " + df.get("body_for_model", "").fillna("").astype(str)
    )


def load_dataset(dataset_path: str, target_column: str):
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
    df = df[df[target_column].isin(VALID_LABELS)].copy()

    # ใช้ text_input เดิมถ้ามี ไม่งั้นสร้างใหม่
    if "text_input" not in df.columns:
        df["text_input"] = build_text_input(df)

    df["text_input"] = df["text_input"].fillna("").astype(str).str.strip()
    df = df[df["text_input"] != ""].copy()

    # สร้าง logic feature text
    df = build_logic_features(df)

    # สร้างคอลัมน์ rule label
    rule_outputs = df.apply(detect_rule_label, axis=1)
    df["rule_label"] = [x[0] for x in rule_outputs]
    df["rule_source"] = [x[1] for x in rule_outputs]

    # ใช้ train จริง
    df["combined_features"] = (
        df["text_input"].fillna("").astype(str) + " ||| " +
        df["logic_text"].fillna("").astype(str)
    )

    # ใช้ explain / feature importance แบบอ่านง่าย
    df["explain_text_features"] = (
        "TICKET_TYPE: " + df.get("ticket_type", "").fillna("").astype(str) + " ||| " +
        "TO_ADDRESS: " + df.get("to_address", "").fillna("").astype(str) + " ||| " +
        "SUBJECT: " + df.get("subject_clean", "").fillna("").astype(str) + " ||| " +
        "SHORT_DESC: " + df.get("short_desc_clean", "").fillna("").astype(str) + " ||| " +
        "DETAIL: " + df.get("description_for_model", "").fillna("").astype(str) + " ||| " +
        "ENV: " + df.get("related_env_raw", "").fillna("").astype(str) + " ||| " +
        "BODY: " + df.get("body_for_model", "").fillna("").astype(str)
    )

    X = df["combined_features"]
    y = df[target_column]

    return df, X, y


# =========================================================
# 5) MODEL FACTORIES
# =========================================================
def build_models():
    common_tfidf = {
        "tokenizer": thai_tokenizer,
        "token_pattern": None,
        "ngram_range": (1, 3),
        "min_df": 2,
        "max_df": 0.97,
        "use_idf": True,
        "sublinear_tf": True,
    }

    alt_tfidf = {
        "tokenizer": thai_tokenizer,
        "token_pattern": None,
        "ngram_range": (1, 4),
        "min_df": 1,
        "max_df": 0.98,
        "use_idf": True,
        "sublinear_tf": True,
    }

    models = {
        "logistic_regression_balanced": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", LogisticRegression(
                class_weight="balanced",
                C=2.0,
                max_iter=3000,
                random_state=RANDOM_STATE
            ))
        ]),
        "logistic_regression_l2_alt": Pipeline([
            ("tfidf", TfidfVectorizer(**alt_tfidf)),
            ("clf", LogisticRegression(
                class_weight="balanced",
                C=4.0,
                max_iter=3000,
                random_state=RANDOM_STATE
            ))
        ]),
        "linear_svc_raw": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", LinearSVC(
                class_weight="balanced",
                C=1.5,
                random_state=RANDOM_STATE
            ))
        ]),
        "linear_svc_calibrated": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", CalibratedClassifierCV(
                estimator=LinearSVC(
                    class_weight="balanced",
                    C=1.5,
                    random_state=RANDOM_STATE
                ),
                cv=3
            ))
        ]),
        "sgd_hinge": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", SGDClassifier(
                loss="hinge",
                alpha=1e-5,
                class_weight="balanced",
                max_iter=3000,
                tol=1e-3,
                random_state=RANDOM_STATE
            ))
        ]),
        "sgd_log_loss": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", SGDClassifier(
                loss="log_loss",
                alpha=1e-5,
                class_weight="balanced",
                max_iter=3000,
                tol=1e-3,
                random_state=RANDOM_STATE
            ))
        ]),
        "ridge_classifier": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", RidgeClassifier(
                class_weight="balanced"
            ))
        ]),
        "multinomial_nb": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", MultinomialNB(alpha=0.5))
        ]),
        "complement_nb": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", ComplementNB(alpha=0.3))
        ]),
        "bernoulli_nb": Pipeline([
            ("tfidf", TfidfVectorizer(
                **common_tfidf,
                binary=True
            )),
            ("clf", BernoulliNB(alpha=0.3))
        ]),
        "random_forest": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", RandomForestClassifier(
                n_estimators=300,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1
            ))
        ]),
        "extra_trees": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", ExtraTreesClassifier(
                n_estimators=400,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1
            ))
        ]),
    }

    return models


# =========================================================
# 6) EVALUATE SINGLE MODELS
# =========================================================
def evaluate_models(X, y):
    models = build_models()
    results = []

    print("📦 Dataset summary")
    print(f"Rows: {len(X)}")
    print(f"Classes: {y.nunique()}")
    print("\n📊 Label distribution:")
    print(y.value_counts())
    print("-" * 80)

    min_class_count = y.value_counts().min()
    if min_class_count < 2:
        raise ValueError("มีบาง class ข้อมูลน้อยกว่า 2 แถว ไม่สามารถทำ StratifiedKFold ได้")

    n_splits = min(10, min_class_count)
    if n_splits < 2:
        raise ValueError("ข้อมูลต่อ class น้อยเกินไปสำหรับ cross-validation")

    cv = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    scoring = {
        "accuracy": "accuracy",
        "f1_macro": "f1_macro",
        "f1_weighted": "f1_weighted"
    }

    trained_models = {}

    for model_name, model in models.items():
        print(f"\n⏳ Cross-validating model: {model_name}")

        cv_results = cross_validate(
            model,
            X,
            y,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
            error_score="raise"
        )

        mean_acc = cv_results["test_accuracy"].mean()
        std_acc = cv_results["test_accuracy"].std()

        mean_macro_f1 = cv_results["test_f1_macro"].mean()
        std_macro_f1 = cv_results["test_f1_macro"].std()

        mean_weighted_f1 = cv_results["test_f1_weighted"].mean()
        std_weighted_f1 = cv_results["test_f1_weighted"].std()

        print(f"Accuracy     : {mean_acc:.4f} ± {std_acc:.4f}")
        print(f"Macro F1     : {mean_macro_f1:.4f} ± {std_macro_f1:.4f}")
        print(f"Weighted F1  : {mean_weighted_f1:.4f} ± {std_weighted_f1:.4f}")

        model.fit(X, y)
        trained_models[model_name] = model

        results.append({
            "model_name": model_name,
            "cv_folds": n_splits,
            "accuracy_mean": mean_acc,
            "accuracy_std": std_acc,
            "macro_f1_mean": mean_macro_f1,
            "macro_f1_std": std_macro_f1,
            "weighted_f1_mean": mean_weighted_f1,
            "weighted_f1_std": std_weighted_f1,
            "rows": len(X),
            "num_classes": y.nunique()
        })

    results_df = (
        pd.DataFrame(results)
        .sort_values(by=["macro_f1_mean", "accuracy_mean"], ascending=False)
        .reset_index(drop=True)
    )

    best_model_name = results_df.iloc[0]["model_name"]
    best_model = trained_models[best_model_name]

    return results_df, best_model_name, best_model, trained_models


# =========================================================
# 7) ENSEMBLE / HYBRID BUNDLE
# =========================================================
@dataclass
class HybridBundle:
    best_model_name: str
    best_model: object
    top_model_names: List[str]
    top_models: Dict[str, object]
    labels: List[str]


def build_hybrid_bundle(results_df: pd.DataFrame, trained_models: Dict[str, object], best_model_name: str, best_model) -> HybridBundle:
    top_model_names = results_df.head(min(5, len(results_df)))["model_name"].tolist()
    top_models = {name: trained_models[name] for name in top_model_names}

    labels = sorted(list(VALID_LABELS))

    return HybridBundle(
        best_model_name=best_model_name,
        best_model=best_model,
        top_model_names=top_model_names,
        top_models=top_models,
        labels=labels
    )


# =========================================================
# 8) FUTURE INFERENCE HELPERS
# =========================================================
def predict_with_rules_first(row_dict: Dict, bundle: HybridBundle):
    row = pd.Series(row_dict)
    rule_label, rule_source = detect_rule_label(row)

    if rule_label:
        return {
            "predicted_label": rule_label,
            "prediction_source": rule_source,
            "used_rule": True,
            "confidence": 1.0,
            "is_low_confidence": False
        }

    logic_df = build_logic_features(pd.DataFrame([row_dict]))
    combined_text = (
        safe_text(row_dict.get("text_input")) + " ||| " +
        safe_text(logic_df.iloc[0]["logic_text"])
    )

    votes = []
    confidences = []

    for model_name, model in bundle.top_models.items():
        pred = model.predict([combined_text])[0]
        votes.append(pred)

        # ถ้ามี predict_proba ใช้ confidence ได้
        if hasattr(model, "predict_proba"):
            try:
                probs = model.predict_proba([combined_text])[0]
                confidences.append(float(np.max(probs)))
            except Exception:
                pass

    vote_counter = Counter(votes)
    voted_label, vote_count = vote_counter.most_common(1)[0]

    avg_confidence = float(np.mean(confidences)) if confidences else vote_count / max(len(votes), 1)
    is_low_confidence = avg_confidence < CONFIDENCE_THRESHOLD

    return {
        "predicted_label": voted_label,
        "prediction_source": f"ensemble_vote_{vote_count}_of_{len(votes)}",
        "used_rule": False,
        "votes": dict(vote_counter),
        "confidence": avg_confidence,
        "is_low_confidence": is_low_confidence
    }


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


def resolve_two_task_case(records: List[Dict], bundle: HybridBundle):
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

        # keyword score เพิ่มเติม
        row1_aws_score = score_row_for_team(row1["row"], "AWS Team")
        row1_gcp_score = score_row_for_team(row1["row"], "GCP Team")
        row2_aws_score = score_row_for_team(row2["row"], "AWS Team")
        row2_gcp_score = score_row_for_team(row2["row"], "GCP Team")

        # 1) ถ้ามี explicit rule แค่ตัวเดียว -> อีกตัวเป็น opposite ทันที
        if used_rule1 and not used_rule2:
            row2["pred"]["predicted_label"] = "AWS Team" if pred1 == "GCP Team" else "GCP Team"
            row2["pred"]["prediction_source"] = "two_task_opposite_inference_from_rule"

        elif used_rule2 and not used_rule1:
            row1["pred"]["predicted_label"] = "AWS Team" if pred2 == "GCP Team" else "GCP Team"
            row1["pred"]["prediction_source"] = "two_task_opposite_inference_from_rule"

        # 2) ถ้าทั้งคู่เป็น rule แต่เหมือนกันผิดธรรมชาติ ให้ดู keyword score แล้ว flip ตัวที่อ่อนกว่า
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

        # 3) ถ้าทั้งคู่ไม่ใช่ rule และทายเหมือนกัน -> ดู score ก่อน, ถ้ายังเสมอค่อยใช้ confidence flip
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

        # 4) ถ้าคนหนึ่ง confidence ต่ำ อีกคนสูงมาก ใช้ opposite
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


def save_feature_importance(best_model_name: str, best_model, output_path: str, top_k: int = 200):
    if best_model_name not in ["extra_trees", "random_forest"]:
        print(f"ℹ️ Skip feature importance เพราะ model '{best_model_name}' ไม่รองรับ feature_importances_")
        return

    try:
        vectorizer = best_model.named_steps["tfidf"]
        clf = best_model.named_steps["clf"]

        if not hasattr(clf, "feature_importances_"):
            print(f"ℹ️ Model '{best_model_name}' ไม่มี feature_importances_")
            return

        feature_names = vectorizer.get_feature_names_out()
        importances = clf.feature_importances_

        fi = pd.DataFrame({
            "feature": feature_names,
            "importance": importances
        }).sort_values("importance", ascending=False)

        fi.head(top_k).to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ Saved feature importance -> {output_path}")

    except Exception as e:
        print(f"⚠️ Save feature importance failed: {e}")


# =========================================================
# 9) MAIN
# =========================================================
def train_explain_model(df: pd.DataFrame, target_column: str):
    explain_X = df["explain_text_features"].fillna("").astype(str)
    explain_y = df[target_column].astype(str)

    explain_model = Pipeline([
        ("tfidf", TfidfVectorizer(
            tokenizer=thai_tokenizer,
            token_pattern=None,
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.97,
            use_idf=True,
            sublinear_tf=True,
        )),
        ("clf", ExtraTreesClassifier(
            n_estimators=400,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1
        ))
    ])

    explain_model.fit(explain_X, explain_y)
    return explain_model


def main():
    print("🚀 Start training model comparison")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Target: {TARGET_COLUMN}")
    print("-" * 80)

    df, X, y = load_dataset(DATASET_PATH, TARGET_COLUMN)

    if len(df) < 10:
        raise ValueError("ข้อมูลน้อยเกินไปสำหรับ training")

    print("\n📌 Rule coverage on training data")
    unmatched_df = df[df["rule_label"].isna()].copy()
    if not unmatched_df.empty:
        unmatched_df.to_csv(Config.RULE_UNMATCHED_CASES_PATH, index=False, encoding="utf-8-sig")
        print(f"🧩 Saved unmatched rule cases -> {Config.RULE_UNMATCHED_CASES_PATH} ({len(unmatched_df)} rows)")
    rule_covered = df["rule_label"].notna().sum()
    print(f"Rows matched by rules: {rule_covered}/{len(df)} ({rule_covered/len(df):.2%})")
    if rule_covered > 0:
        print(df["rule_source"].value_counts(dropna=False).head(20))

    results_df, best_model_name, best_model, trained_models = evaluate_models(X, y)

    print("\n🏆 Model comparison summary")
    print(results_df)

    results_df.to_csv(REPORT_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n📝 Saved comparison report to: {REPORT_OUTPUT_PATH}")

    joblib.dump(best_model, MODEL_OUTPUT_PATH)
    print(f"✅ Saved best single model: {best_model_name} -> {MODEL_OUTPUT_PATH}")

    # 1) importance จาก model จริงที่ train บน combined_features
    save_feature_importance(
        best_model_name,
        best_model,
        FEATURE_IMPORTANCE_OUTPUT_PATH,
        top_k=200
    )

    # 2) importance จาก explain model ที่ train บน text จริงล้วน
    explain_model = train_explain_model(df, TARGET_COLUMN)
    save_feature_importance(
        "extra_trees",
        explain_model,
        EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH,
        top_k=200
    )

    bundle = build_hybrid_bundle(results_df, trained_models, best_model_name, best_model)
    joblib.dump(bundle, ENSEMBLE_OUTPUT_PATH)
    print(f"✅ Saved hybrid ensemble bundle -> {ENSEMBLE_OUTPUT_PATH}")


if __name__ == "__main__":
    main()