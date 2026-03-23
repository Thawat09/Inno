import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import ExtraTreesClassifier

from app.utils.ml_utils import thai_tokenizer
from model.train_settings import (
    RANDOM_STATE,
    CONFIDENCE_THRESHOLD,
)
from model.train_helpers import safe_text
from model.rule_engine import (
    detect_rule_label,
    build_logic_features,
    rebuild_text_input_for_row,
)
from model.model_factory import (
    build_models,
    build_default_model,
    SingleLabelModel,
)


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
# 7) FUTURE INFERENCE HELPERS
# =========================================================
def predict_best_single_model_row(row_dict: dict, best_model) -> dict:
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


def predict_with_rules_first(row_dict: dict, bundle):
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

    vote_counter = dict()
    for v in votes:
        vote_counter[v] = vote_counter.get(v, 0) + 1
    voted_label, vote_count = sorted(vote_counter.items(), key=lambda x: x[1], reverse=True)[0]

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