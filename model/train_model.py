import os
import sys
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB

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
    """
    สร้างข้อความรวมจากคอลัมน์ล่าสุดของ dataset
    """
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


def load_dataset(dataset_path: str, target_column: str) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ dataset: {dataset_path}")

    df = pd.read_csv(dataset_path)

    if target_column not in df.columns:
        raise ValueError(
            f"ไม่พบคอลัมน์ target '{target_column}' ในไฟล์ {dataset_path}\n"
            f"columns ที่มี: {list(df.columns)}"
        )

    # ลบแถวที่ target ว่าง
    df = df.dropna(subset=[target_column]).copy()
    df[target_column] = df[target_column].astype(str).str.strip()

    # ลบ target ว่าง
    df = df[df[target_column] != ""].copy()

    # สร้าง text input
    df["combined_features"] = build_text_input(df)

    # ลบแถวที่ text ว่าง
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
        "linear_svc": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", LinearSVC(
                class_weight="balanced",
                random_state=RANDOM_STATE
            ))
        ]),
        "multinomial_nb": Pipeline([
            ("tfidf", TfidfVectorizer(**common_tfidf)),
            ("clf", MultinomialNB())
        ]),
    }

    return models


# =========================================================
# 4) TRAIN / EVALUATE
# =========================================================
def evaluate_models(X, y):
    """
    train/test split แล้วเทียบ 3 model
    """
    # ถ้า class ไหนมีน้อยมาก stratify อาจพัง
    use_stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=use_stratify
    )

    models = build_models()
    results = []
    trained_models = {}

    print("📦 Dataset summary")
    print(f"Rows: {len(X)}")
    print(f"Classes: {y.nunique()}")
    print("\n📊 Label distribution:")
    print(y.value_counts())
    print("-" * 70)

    for model_name, model in models.items():
        print(f"\n⏳ Training model: {model_name}")
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        print(f"\n📊 Report for: {model_name}")
        print(f"Accuracy: {acc * 100:.2f}%")
        print(classification_report(y_test, y_pred, zero_division=0))

        results.append({
            "model_name": model_name,
            "accuracy": acc,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "num_classes": y.nunique()
        })

        trained_models[model_name] = model

    results_df = pd.DataFrame(results).sort_values(by="accuracy", ascending=False).reset_index(drop=True)
    best_model_name = results_df.iloc[0]["model_name"]
    best_model = trained_models[best_model_name]

    return results_df, best_model_name, best_model


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
        raise ValueError("ข้อมูลน้อยเกินไปสำหรับ train/test split")

    results_df, best_model_name, best_model = evaluate_models(X, y)

    print("\n🏆 Model comparison summary")
    print(results_df)

    results_df.to_csv(REPORT_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n📝 Saved comparison report to: {REPORT_OUTPUT_PATH}")

    joblib.dump(best_model, MODEL_OUTPUT_PATH)
    print(f"✅ Saved best model: {best_model_name} -> {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()

# TODO ---------------------------------- new version train

# import os
# import sys
# import joblib
# import pandas as pd

# from sklearn.model_selection import train_test_split
# from sklearn.pipeline import Pipeline
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics import accuracy_score, classification_report, f1_score
# from sklearn.linear_model import LogisticRegression
# from sklearn.svm import LinearSVC
# from sklearn.naive_bayes import MultinomialNB
# from sklearn.calibration import CalibratedClassifierCV

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
# if PROJECT_ROOT not in sys.path:
#     sys.path.append(PROJECT_ROOT)

# from app.utils.ml_utils import thai_tokenizer


# # =========================================================
# # 1) CONFIG
# # =========================================================
# # TODO: train สำหรับ Cloud Sub-Team
# DATASET_PATH = "ticket_training_cloud_sub_team.csv"
# TARGET_COLUMN = "label_sub_team"
# MODEL_OUTPUT_PATH = "best_ticket_classifier_model.pkl"
# REPORT_OUTPUT_PATH = "model_comparison_results.csv"

# # # TODO: train สำหรับ Cloud Main-Team
# # DATASET_PATH = "ticket_training_main_team.csv"
# # TARGET_COLUMN = "label_main_team"
# # MODEL_OUTPUT_PATH = "best_main_team_model.pkl"
# # REPORT_OUTPUT_PATH = "main_team_model_comparison_results.csv"

# TEST_SIZE = 0.2
# RANDOM_STATE = 42


# # =========================================================
# # 2) DATA PREP
# # =========================================================
# def build_text_input(df: pd.DataFrame) -> pd.Series:
#     return (
#         "TICKET_TYPE: " + df.get("ticket_type", "").fillna("").astype(str) + " ||| " +
#         "TO_ADDRESS: " + df.get("to_address", "").fillna("").astype(str) + " ||| " +
#         "SUBJECT: " + df.get("subject_clean", "").fillna("").astype(str) + " ||| " +
#         "TASK_DESC: " + df.get("task_short_desc", "").fillna("").astype(str) + " ||| " +
#         "RITM_DESC: " + df.get("ritm_short_desc", "").fillna("").astype(str) + " ||| " +
#         "DETAIL: " + df.get("description", "").fillna("").astype(str) + " ||| " +
#         "ENV: " + df.get("related_env_raw", "").fillna("").astype(str) + " ||| " +
#         "BODY: " + df.get("body_text_clean", "").fillna("").astype(str)
#     )


# def load_dataset(dataset_path: str, target_column: str):
#     if not os.path.exists(dataset_path):
#         raise FileNotFoundError(f"ไม่พบไฟล์ dataset: {dataset_path}")

#     df = pd.read_csv(dataset_path)

#     if target_column not in df.columns:
#         raise ValueError(
#             f"ไม่พบคอลัมน์ target '{target_column}' ในไฟล์ {dataset_path}\n"
#             f"columns ที่มี: {list(df.columns)}"
#         )

#     df = df.dropna(subset=[target_column]).copy()
#     df[target_column] = df[target_column].astype(str).str.strip()
#     df = df[df[target_column] != ""].copy()

#     df["combined_features"] = build_text_input(df)
#     df["combined_features"] = df["combined_features"].fillna("").astype(str).str.strip()
#     df = df[df["combined_features"] != ""].copy()

#     X = df["combined_features"]
#     y = df[target_column]

#     return df, X, y


# # =========================================================
# # 3) MODEL FACTORIES
# # =========================================================
# def build_models():
#     common_tfidf = {
#         "tokenizer": thai_tokenizer,
#         "token_pattern": None,
#         "ngram_range": (1, 3),
#         "min_df": 2,
#         "max_df": 0.95,
#         "use_idf": True,
#         "sublinear_tf": True,
#     }

#     models = {
#         "logistic_regression": Pipeline([
#             ("tfidf", TfidfVectorizer(**common_tfidf)),
#             ("clf", LogisticRegression(
#                 class_weight="balanced",
#                 max_iter=2000,
#                 random_state=RANDOM_STATE
#             ))
#         ]),
#         "linear_svc_calibrated": Pipeline([
#             ("tfidf", TfidfVectorizer(**common_tfidf)),
#             ("clf", CalibratedClassifierCV(
#                 estimator=LinearSVC(
#                     class_weight="balanced",
#                     random_state=RANDOM_STATE
#                 ),
#                 cv=3
#             ))
#         ]),
#         "multinomial_nb": Pipeline([
#             ("tfidf", TfidfVectorizer(**common_tfidf)),
#             ("clf", MultinomialNB())
#         ]),
#     }

#     return models


# # =========================================================
# # 4) TRAIN / EVALUATE
# # =========================================================
# def evaluate_models(X, y):
#     use_stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None

#     X_train, X_test, y_train, y_test = train_test_split(
#         X,
#         y,
#         test_size=TEST_SIZE,
#         random_state=RANDOM_STATE,
#         stratify=use_stratify
#     )

#     models = build_models()
#     results = []
#     trained_models = {}

#     print("📦 Dataset summary")
#     print(f"Rows: {len(X)}")
#     print(f"Classes: {y.nunique()}")
#     print("\n📊 Label distribution:")
#     print(y.value_counts())
#     print("-" * 70)

#     for model_name, model in models.items():
#         print(f"\n⏳ Training model: {model_name}")
#         model.fit(X_train, y_train)

#         y_pred = model.predict(X_test)
#         acc = accuracy_score(y_test, y_pred)
#         macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
#         weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

#         print(f"\n📊 Report for: {model_name}")
#         print(f"Accuracy: {acc * 100:.2f}%")
#         print(f"Macro F1: {macro_f1:.4f}")
#         print(f"Weighted F1: {weighted_f1:.4f}")
#         print(classification_report(y_test, y_pred, zero_division=0))

#         results.append({
#             "model_name": model_name,
#             "accuracy": acc,
#             "macro_f1": macro_f1,
#             "weighted_f1": weighted_f1,
#             "train_rows": len(X_train),
#             "test_rows": len(X_test),
#             "num_classes": y.nunique()
#         })

#         trained_models[model_name] = model

#     # ใช้ macro_f1 ก่อน แล้วค่อยดู accuracy
#     results_df = (
#         pd.DataFrame(results)
#         .sort_values(by=["macro_f1", "accuracy"], ascending=False)
#         .reset_index(drop=True)
#     )

#     best_model_name = results_df.iloc[0]["model_name"]
#     best_model = trained_models[best_model_name]

#     return results_df, best_model_name, best_model


# # =========================================================
# # 5) MAIN
# # =========================================================
# def main():
#     print("🚀 Start training model comparison")
#     print(f"Dataset: {DATASET_PATH}")
#     print(f"Target: {TARGET_COLUMN}")
#     print("-" * 70)

#     df, X, y = load_dataset(DATASET_PATH, TARGET_COLUMN)

#     if len(df) < 10:
#         raise ValueError("ข้อมูลน้อยเกินไปสำหรับ train/test split")

#     results_df, best_model_name, best_model = evaluate_models(X, y)

#     print("\n🏆 Model comparison summary")
#     print(results_df)

#     results_df.to_csv(REPORT_OUTPUT_PATH, index=False, encoding="utf-8-sig")
#     print(f"\n📝 Saved comparison report to: {REPORT_OUTPUT_PATH}")

#     joblib.dump(best_model, MODEL_OUTPUT_PATH)
#     print(f"✅ Saved best model: {best_model_name} -> {MODEL_OUTPUT_PATH}")


# if __name__ == "__main__":
#     main()