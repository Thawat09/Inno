import os
import re
import sys
import joblib
import numpy as np
import pandas as pd

from datetime import datetime
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression, SGDClassifier, RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB, ComplementNB, BernoulliNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.config import Config
from app.utils.ml_utils import thai_tokenizer


# =========================================================
# 1) GLOBAL CONFIG
# =========================================================
TEST_SIZE = Config.ML_TEST_SIZE
RANDOM_STATE = Config.ML_RANDOM_STATE
CONFIDENCE_THRESHOLD = Config.ML_CONFIDENCE_THRESHOLD

AWS_KEYWORDS = list(Config.AWS_KEYWORDS) + list(Config.EXTRA_AWS_KEYWORDS)
GCP_KEYWORDS = list(Config.GCP_KEYWORDS) + list(Config.EXTRA_GCP_KEYWORDS)
SYSTEM_MAPPING = getattr(Config, "SYSTEM_MAPPING", {})


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


def count_keyword_hits(text: str, keywords: List[str]) -> int:
    if not text:
        return 0
    text_upper = text.upper()
    return sum(1 for k in keywords if str(k).upper() in text_upper)


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


# =========================================================
# 4) MODEL FACTORIES
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

    return {
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
        "decision_tree": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", DecisionTreeClassifier(
                class_weight="balanced",
                random_state=RANDOM_STATE,
                max_depth=30,
                min_samples_split=5,
                min_samples_leaf=2
            ))
        ]),
    }


def build_default_model():
    common_tfidf = {
        "tokenizer": thai_tokenizer,
        "token_pattern": None,
        "ngram_range": (1, 3),
        "min_df": 2,
        "max_df": 0.97,
        "use_idf": True,
        "sublinear_tf": True,
    }

    return Pipeline([
        ("tfidf", TfidfVectorizer(**common_tfidf)),
        ("clf", LogisticRegression(
            class_weight="balanced",
            C=2.0,
            max_iter=3000,
            random_state=RANDOM_STATE
        ))
    ])


# =========================================================
# 5) TRAIN / EVALUATE
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


@dataclass
class SingleLabelModel:
    label: str

    def predict(self, X):
        return np.array([self.label] * len(X))

    def predict_proba(self, X):
        return np.array([[1.0] for _ in range(len(X))])


def train_single_model(X, y):
    print("📦 Dataset summary")
    print(f"Rows: {len(X)}")
    print(f"Classes: {y.nunique()}")
    print("\n📊 Label distribution:")
    print(y.value_counts())
    print("-" * 80)

    unique_labels = sorted(y.astype(str).unique().tolist())

    if len(unique_labels) == 1:
        only_label = unique_labels[0]
        print(f"⚠️ พบข้อมูลเพียง class เดียว: {only_label}")
        print("ℹ️ ใช้ SingleLabelModel แทน sklearn classifier")

        model = SingleLabelModel(label=only_label)
        trained_models = {"single_label_model": model}

        results_df = pd.DataFrame([{
            "model_name": "single_label_model",
            "rows": len(X),
            "num_classes": 1,
            "train_accuracy": 1.0,
            "train_macro_f1": 1.0,
            "train_weighted_f1": 1.0,
            "note": f"only one class found: {only_label}"
        }])

        return results_df, "single_label_model", model, trained_models

    model = build_default_model()
    print("🚀 Training single model: logistic_regression_balanced")
    model.fit(X, y)

    y_pred = model.predict(X)
    train_acc = accuracy_score(y, y_pred)
    train_macro_f1 = f1_score(y, y_pred, average="macro")
    train_weighted_f1 = f1_score(y, y_pred, average="weighted")

    trained_models = {"logistic_regression_balanced": model}

    results_df = pd.DataFrame([{
        "model_name": "logistic_regression_balanced",
        "rows": len(X),
        "num_classes": y.nunique(),
        "train_accuracy": train_acc,
        "train_macro_f1": train_macro_f1,
        "train_weighted_f1": train_weighted_f1,
        "note": "trained without cross-validation"
    }])

    return results_df, "logistic_regression_balanced", model, trained_models


# =========================================================
# 6) ENSEMBLE / HYBRID BUNDLE
# =========================================================
@dataclass
class HybridBundle:
    best_model_name: str
    best_model: object
    top_model_names: List[str]
    top_models: Dict[str, object]
    labels: List[str]


def build_hybrid_bundle(
    results_df: pd.DataFrame,
    trained_models: Dict[str, object],
    best_model_name: str,
    best_model,
    labels: List[str]
) -> HybridBundle:
    top_model_names = [name for name in results_df["model_name"].tolist() if name in trained_models]

    if not top_model_names:
        top_model_names = [best_model_name]

    top_models = {name: trained_models[name] for name in top_model_names}

    return HybridBundle(
        best_model_name=best_model_name,
        best_model=best_model,
        top_model_names=top_model_names,
        top_models=top_models,
        labels=sorted(labels)
    )


# =========================================================
# 7) FUTURE INFERENCE HELPERS
# =========================================================
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


def predict_best_single_model_row(row_dict: Dict, best_model) -> Dict:
    row_copy = dict(row_dict)

    if not safe_text(row_copy.get("text_input")):
        row_copy["text_input"] = rebuild_text_input_for_row(row_copy)

    logic_df = build_logic_features(pd.DataFrame([row_copy]))
    combined_text = (
        safe_text(row_copy.get("text_input")) + " ||| " +
        safe_text(logic_df.iloc[0]["logic_text"])
    )

    predicted_label = best_model.predict([combined_text])[0]

    confidence = None
    is_low_confidence = None

    if hasattr(best_model, "predict_proba"):
        try:
            probs = best_model.predict_proba([combined_text])[0]
            confidence = float(np.max(probs))
            is_low_confidence = confidence < CONFIDENCE_THRESHOLD
        except Exception:
            confidence = None
            is_low_confidence = None

    return {
        "predicted_label": predicted_label,
        "prediction_source": "best_single_model",
        "confidence": confidence,
        "is_low_confidence": is_low_confidence
    }


def predict_with_rules_first(row_dict: Dict, bundle: HybridBundle):
    row = pd.Series(row_dict)
    valid_labels = set(bundle.labels)
    rule_label, rule_source = detect_rule_label(row, valid_labels)

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
# 8) TRAIN EXPLAIN MODEL
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


# =========================================================
# 9) TRAIN PIPELINE - CLOUD SUBTEAM
# =========================================================
def run_training_pipeline_cloud(
    dataset_path: str,
    target_column: str,
    valid_labels: Set[str],
    model_output_path: str,
    ensemble_output_path: str,
    report_output_path: str,
    feature_importance_output_path: str,
    explain_feature_importance_output_path: str,
    unmatched_cases_output_path: str,
    model_base_name: str,
    enable_rules: bool = True,
):
    print("🚀 Start training CLOUD SUBTEAM model")
    print(f"Dataset: {dataset_path}")
    print(f"Target: {target_column}")
    print(f"Valid labels: {sorted(valid_labels)}")
    print(f"Enable rules: {enable_rules}")
    print("-" * 80)

    df, X, y = load_dataset(
        dataset_path=dataset_path,
        target_column=target_column,
        valid_labels=valid_labels,
        enable_rules=enable_rules
    )

    if len(df) < 10:
        raise ValueError("ข้อมูลน้อยเกินไปสำหรับ training")

    if enable_rules:
        print("\n📌 Rule coverage on training data")
        unmatched_df = df[df["rule_label"].isna()].copy()
        if not unmatched_df.empty:
            unmatched_df.to_csv(unmatched_cases_output_path, index=False, encoding="utf-8-sig")
            print(f"🧩 Saved unmatched rule cases -> {unmatched_cases_output_path} ({len(unmatched_df)} rows)")

        rule_covered = df["rule_label"].notna().sum()
        print(f"Rows matched by rules: {rule_covered}/{len(df)} ({rule_covered / len(df):.2%})")
        if rule_covered > 0:
            print(df["rule_source"].value_counts(dropna=False).head(20))

    results_df, best_model_name, best_model, trained_models = evaluate_models(X, y)

    print("\n🏆 Model comparison summary")
    print(results_df)

    results_df.to_csv(report_output_path, index=False, encoding="utf-8-sig")
    print(f"\n📝 Saved comparison report to: {report_output_path}")

    joblib.dump(best_model, model_output_path)
    print(f"✅ Saved best single model: {best_model_name} -> {model_output_path}")

    backup_path = get_versioned_model_path(model_base_name, model_output_path)
    joblib.dump(best_model, backup_path)
    print(f"📦 Backup model saved to: {backup_path}")

    save_feature_importance(
        best_model_name=best_model_name,
        best_model=best_model,
        output_path=feature_importance_output_path,
        top_k=200
    )

    explain_model = train_explain_model(df, target_column)
    save_feature_importance(
        best_model_name="extra_trees",
        best_model=explain_model,
        output_path=explain_feature_importance_output_path,
        top_k=200
    )

    bundle = build_hybrid_bundle(
        results_df=results_df,
        trained_models=trained_models,
        best_model_name=best_model_name,
        best_model=best_model,
        labels=list(valid_labels)
    )
    joblib.dump(bundle, ensemble_output_path)
    print(f"✅ Saved hybrid ensemble bundle -> {ensemble_output_path}")

    print("✅ Skip best-vs-bundle evaluation for speed")


# =========================================================
# 10) TRAIN PIPELINE - MAIN TEAM
# =========================================================
def run_training_pipeline_main(
    dataset_path: str,
    target_column: str,
    valid_labels: Set[str],
    model_output_path: str,
    ensemble_output_path: str,
    report_output_path: str,
    feature_importance_output_path: str,
    explain_feature_importance_output_path: str,
    unmatched_cases_output_path: str,
    model_base_name: str,
    enable_rules: bool = False,
):
    print("🚀 Start training MAIN TEAM model")
    print(f"Dataset: {dataset_path}")
    print(f"Target: {target_column}")
    print(f"Valid labels: {sorted(valid_labels)}")
    print(f"Enable rules: {enable_rules}")
    print("-" * 80)

    df, X, y = load_dataset(
        dataset_path=dataset_path,
        target_column=target_column,
        valid_labels=valid_labels,
        enable_rules=enable_rules
    )

    if len(df) < 1:
        raise ValueError("ไม่มีข้อมูลสำหรับ training")

    print("\n📌 Rule coverage skipped for main team pipeline")

    results_df, best_model_name, best_model, trained_models = train_single_model(X, y)

    print("\n🏆 Training summary")
    print(results_df)

    results_df.to_csv(report_output_path, index=False, encoding="utf-8-sig")
    print(f"\n📝 Saved training report to: {report_output_path}")

    joblib.dump(best_model, model_output_path)
    print(f"✅ Saved model: {best_model_name} -> {model_output_path}")

    backup_path = get_versioned_model_path(model_base_name, model_output_path)
    joblib.dump(best_model, backup_path)
    print(f"📦 Backup model saved to: {backup_path}")

    if best_model_name in ["extra_trees", "random_forest"]:
        save_feature_importance(
            best_model_name=best_model_name,
            best_model=best_model,
            output_path=feature_importance_output_path,
            top_k=200
        )
    else:
        print(f"ℹ️ Skip feature importance for model: {best_model_name}")

    if y.nunique() >= 2:
        explain_model = train_explain_model(df, target_column)
        save_feature_importance(
            best_model_name="extra_trees",
            best_model=explain_model,
            output_path=explain_feature_importance_output_path,
            top_k=200
        )
    else:
        print("ℹ️ Skip explain model because dataset has only one class")

    bundle = build_hybrid_bundle(
        results_df=results_df,
        trained_models=trained_models,
        best_model_name=best_model_name,
        best_model=best_model,
        labels=list(valid_labels)
    )
    joblib.dump(bundle, ensemble_output_path)
    print(f"✅ Saved bundle -> {ensemble_output_path}")

    print("✅ Main team pipeline trained without cross-validation")


# =========================================================
# 11) MAIN
# =========================================================
def main():
    cloud_valid_labels = {
        x.strip()
        for x in Config.VALID_CLOUD_SUBTEAM_LABELS.split(",")
        if x.strip()
    }

    main_valid_labels = {
        x.strip()
        for x in getattr(
            Config,
            "VALID_MAIN_TEAM_LABELS",
            "iNET Cloud Support Team,iNET Network Team,iNET Operation Team"
        ).split(",")
        if x.strip()
    }

    print("========== TRAIN CLOUD SUBTEAM ==========")
    run_training_pipeline_cloud(
        dataset_path=Config.TRAINING_CLOUD_SUBTEAM_DATASET_PATH,
        target_column=Config.TRAINING_TARGET_COLUMN_CLOUD_SUBTEAM,
        valid_labels=cloud_valid_labels,
        model_output_path=Config.BEST_CLOUD_SUBTEAM_CLASSIFIER_MODEL_PATH,
        ensemble_output_path=Config.ENSEMBLE_CLOUD_SUBTEAM_BUNDLE_PATH,
        report_output_path=Config.CLOUD_SUBTEAM_MODEL_COMPARISON_REPORT_PATH,
        feature_importance_output_path=Config.CLOUD_SUBTEAM_FEATURE_IMPORTANCE_OUTPUT_PATH,
        explain_feature_importance_output_path=Config.CLOUD_SUBTEAM_EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH,
        unmatched_cases_output_path=Config.CLOUD_SUBTEAM_RULE_UNMATCHED_CASES_PATH,
        model_base_name="best_cloud_subteam_classifier_model",
        enable_rules=True,
    )

    print("\n========== TRAIN MAIN TEAM ==========")
    run_training_pipeline_main(
        dataset_path=Config.TRAINING_MAIN_TEAM_DATASET_PATH,
        target_column=Config.TRAINING_TARGET_COLUMN_MAIN_TEAM,
        valid_labels=main_valid_labels,
        model_output_path=Config.BEST_MAIN_TEAM_CLASSIFIER_MODEL_PATH,
        ensemble_output_path=Config.ENSEMBLE_MAIN_TEAM_BUNDLE_PATH,
        report_output_path=Config.MAIN_TEAM_MODEL_COMPARISON_REPORT_PATH,
        feature_importance_output_path=Config.MAIN_TEAM_FEATURE_IMPORTANCE_OUTPUT_PATH,
        explain_feature_importance_output_path=Config.MAIN_TEAM_EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH,
        unmatched_cases_output_path=Config.MAIN_TEAM_RULE_UNMATCHED_CASES_PATH,
        model_base_name="best_main_team_classifier_model",
        enable_rules=False,
    )


if __name__ == "__main__":
    main()