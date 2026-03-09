import os
import sys
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import SGDClassifier, RidgeClassifier
from sklearn.naive_bayes import ComplementNB, BernoulliNB
from sklearn.model_selection import StratifiedKFold, cross_validate

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.utils.ml_utils import thai_tokenizer


# =========================================================
# 1) CONFIG
# =========================================================
# TODO: train สำหรับ Cloud Sub-Team
DATASET_PATH = "ticket_training_cloud_sub_team.csv"
TARGET_COLUMN = "label_sub_team"
MODEL_OUTPUT_PATH = "best_ticket_classifier_model.pkl"
REPORT_OUTPUT_PATH = "model_comparison_results.csv"

# # TODO: train สำหรับ Cloud Main-Team
# DATASET_PATH = "ticket_training_main_team.csv"
# TARGET_COLUMN = "label_main_team"
# MODEL_OUTPUT_PATH = "best_main_team_model.pkl"
# REPORT_OUTPUT_PATH = "main_team_model_comparison_results.csv"

TEST_SIZE = 0.2
RANDOM_STATE = 42


# =========================================================
# 2) DATA PREP
# =========================================================
def build_text_input(df: pd.DataFrame) -> pd.Series:
    return (
        "TICKET_TYPE: " + df.get("ticket_type", "").fillna("").astype(str) + " ||| " +
        "TO_ADDRESS: " + df.get("to_address", "").fillna("").astype(str) + " ||| " +
        "SUBJECT: " + df.get("subject_clean", "").fillna("").astype(str) + " ||| " +
        "TASK_DESC: " + df.get("task_short_desc", "").fillna("").astype(str) + " ||| " +
        "RITM_DESC: " + df.get("ritm_short_desc", "").fillna("").astype(str) + " ||| " +
        "DETAIL: " + df.get("description", "").fillna("").astype(str) + " ||| " +
        "ENV: " + df.get("related_env_raw", "").fillna("").astype(str) + " ||| " +
        "BODY: " + df.get("body_text_clean", "").fillna("").astype(str)
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
    df = df[df[target_column] != ""].copy()

    df["combined_features"] = build_text_input(df)
    df["combined_features"] = df["combined_features"].fillna("").astype(str).str.strip()
    df = df[df["combined_features"] != ""].copy()

    X = df["combined_features"]
    y = df[target_column]

    return df, X, y


# =========================================================
# 3) MODEL FACTORIES
# =========================================================
def build_models():
    common_tfidf = {
        "tokenizer": thai_tokenizer,
        "token_pattern": None,
        "ngram_range": (1, 3),
        "min_df": 2,
        "max_df": 0.95,
        "use_idf": True,
        "sublinear_tf": True,
    }

    models = {
        "logistic_regression": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", LogisticRegression(
                class_weight="balanced",
                max_iter=2000,
                random_state=RANDOM_STATE
            ))
        ]),
        "linear_svc_raw": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", LinearSVC(
                class_weight="balanced",
                random_state=RANDOM_STATE
            ))
        ]),
        "linear_svc_calibrated": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", CalibratedClassifierCV(
                estimator=LinearSVC(
                    class_weight="balanced",
                    random_state=RANDOM_STATE
                ),
                cv=3
            ))
        ]),
        "sgd_classifier_hinge": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", SGDClassifier(
                loss="hinge",
                class_weight="balanced",
                max_iter=2000,
                tol=1e-3,
                random_state=RANDOM_STATE
            ))
        ]),
        "sgd_classifier_log_loss": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", SGDClassifier(
                loss="log_loss",
                class_weight="balanced",
                max_iter=2000,
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
            ("clf", MultinomialNB())
        ]),
        "complement_nb": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", ComplementNB())
        ]),
        "bernoulli_nb": Pipeline([
            ("tfidf", TfidfVectorizer(
                **common_tfidf,
                binary=True
            )),
            ("clf", BernoulliNB())
        ]),
        "decision_tree": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", DecisionTreeClassifier(
                class_weight="balanced",
                random_state=RANDOM_STATE
            ))
        ]),
        "random_forest": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1
            ))
        ]),
        "extra_trees": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", ExtraTreesClassifier(
                n_estimators=200,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1
            ))
        ]),
        "knn_5": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", KNeighborsClassifier(
                n_neighbors=5
            ))
        ]),
    }

    return models


# =========================================================
# 4) TRAIN / EVALUATE
# =========================================================
def evaluate_models(X, y):
    models = build_models()
    results = []
    trained_models = {}

    print("📦 Dataset summary")
    print(f"Rows: {len(X)}")
    print(f"Classes: {y.nunique()}")
    print("\n📊 Label distribution:")
    print(y.value_counts())
    print("-" * 70)

    min_class_count = y.value_counts().min()

    if min_class_count < 2:
        raise ValueError(
            "มีบาง class ข้อมูลน้อยกว่า 2 แถว ไม่สามารถทำ StratifiedKFold ได้"
        )

    # n_splits ต้องไม่เกินจำนวนข้อมูลของ class ที่น้อยที่สุด
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
        .sort_values(
            by=["macro_f1_mean", "accuracy_mean"],
            ascending=False
        )
        .reset_index(drop=True)
    )

    best_model_name = results_df.iloc[0]["model_name"]
    best_model = models[best_model_name]

    print(f"\n🏆 Best model from CV: {best_model_name}")
    print("🔁 Fitting best model on full dataset...")

    best_model.fit(X, y)
    trained_models[best_model_name] = best_model

    return results_df, best_model_name, trained_models[best_model_name]


# =========================================================
# 5) MAIN
# =========================================================
def main():
    print("🚀 Start training model comparison")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Target: {TARGET_COLUMN}")
    print("-" * 70)

    df, X, y = load_dataset(DATASET_PATH, TARGET_COLUMN)

    if len(df) < 10:
        raise ValueError("ข้อมูลน้อยเกินไปสำหรับ training")

    results_df, best_model_name, best_model = evaluate_models(X, y)

    print("\n🏆 Model comparison summary")
    print(results_df)

    results_df.to_csv(REPORT_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n📝 Saved comparison report to: {REPORT_OUTPUT_PATH}")

    joblib.dump(best_model, MODEL_OUTPUT_PATH)
    print(f"✅ Saved best model: {best_model_name} -> {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()