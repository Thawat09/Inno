import numpy as np

from dataclasses import dataclass
from typing import Dict, List

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier, RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB, ComplementNB, BernoulliNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier

from app.utils.ml_utils import thai_tokenizer
from model.train_settings import RANDOM_STATE


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


@dataclass
class SingleLabelModel:
    label: str

    def predict(self, X):
        return np.array([self.label] * len(X))

    def predict_proba(self, X):
        return np.array([[1.0] for _ in range(len(X))])


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
    results_df,
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