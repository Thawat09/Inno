import joblib

from app.config import Config
from model.train_helpers import get_versioned_model_path
from model.dataset_builder import load_dataset
from model.model_factory import build_hybrid_bundle
from model.training_engine import (
    evaluate_models,
    train_single_model,
    save_feature_importance,
    train_explain_model,
)


# =========================================================
# 9) TRAIN PIPELINE - CLOUD SUBTEAM
# =========================================================
def run_training_pipeline_cloud(
    dataset_path: str,
    target_column: str,
    valid_labels: set,
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
    valid_labels: set,
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