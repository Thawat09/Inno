import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MODEL_DIR = os.path.join(BASE_DIR, "model")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
EXPORT_DIR = os.path.join(OUTPUT_DIR, "export")
TRAIN_DIR = os.path.join(OUTPUT_DIR, "train")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(TRAIN_DIR, exist_ok=True)

def env_or_default(key, default):
    value = os.getenv(key)
    return value if value not in (None, "") else default

class Config:
    IMAP_SERVER = os.getenv("IMAP_SERVER")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
    LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")

    CHECK_INTERVAL = int(env_or_default("CHECK_INTERVAL", 10))
    TARGET_SENDER = env_or_default("TARGET_SENDER", "SCGTicketSystems@service-now.com")

    DB_URI = os.getenv("DATABASE_URL")

    TARGET_RECEIVER = {
        "scg-wifi@inetms.co.th": "iNET Network Team",
        "scgcloud@inetms.co.th": "iNET Operation Team",
        "inetmscloud@inetms.co.th": "iNET Cloud Support Team",
        "scg_cloud_inet01@scg.com": "iNET Cloud Support Team",
    }

    MAILBOX_FOLDER = env_or_default("MAILBOX_FOLDER", "scg")
    DAYS_BACK = int(env_or_default("DAYS_BACK", 365))
    MAX_EMAILS = int(env_or_default("MAX_EMAILS", "0")) or None
    IMAP_TIMEOUT = int(env_or_default("IMAP_TIMEOUT", 30))

    MASTER_DB_CSV_FILENAME = env_or_default(
        "MASTER_DB_CSV_FILENAME",
        os.path.join(EXPORT_DIR, "ticket_master_db.csv")
    )

    AUDIT_RAW_CSV_FILENAME = env_or_default(
        "AUDIT_RAW_CSV_FILENAME", 
        os.path.join(EXPORT_DIR, "ticket_audit_raw.csv")
    )

    TRAINING_CSV_FILENAME = env_or_default(
        "TRAINING_CSV_FILENAME",
        os.path.join(EXPORT_DIR, "ticket_training_data.csv")
    )

    TRAINING_MAIN_TEAM_CSV_FILENAME = env_or_default(
        "TRAINING_MAIN_TEAM_CSV_FILENAME",
        os.path.join(EXPORT_DIR, "ticket_training_main_team.csv")
    )

    TRAINING_CLOUD_SUBTEAM_CSV_FILENAME = env_or_default(
        "TRAINING_CLOUD_SUBTEAM_CSV_FILENAME",
        os.path.join(EXPORT_DIR, "ticket_training_cloud_sub_team.csv")
    )

    MAX_SUBJECT_LEN = int(env_or_default("MAX_SUBJECT_LEN", 1000))
    MAX_SHORT_DESC_LEN = int(env_or_default("MAX_SHORT_DESC_LEN", 1000))
    MAX_RELATED_ENV_LEN = int(env_or_default("MAX_RELATED_ENV_LEN", 500))
    MAX_DESCRIPTION_LEN = int(env_or_default("MAX_DESCRIPTION_LEN", 5000))
    MAX_BODY_MODEL_LEN = int(env_or_default("MAX_BODY_MODEL_LEN", 12000))

    SYSTEM_MAPPING = {
        "justperformqas.scg.com": "AWS Team",
        "api-justperformqas.scg.com": "AWS Team",
        "tscpcl.outsystemsenterprise.com": "AWS Team",
        "lsp.com": "AWS Team",
        "scgbpc.scg.com": "AWS Team",
        "test-scgbpc.scg.com": "AWS Team",
        "mdm.scg.com": "AWS Team",
        "test-mdm.scg.com": "AWS Team",
        "dev-mdm.scg.com": "AWS Team",
        "swdwd.scg.com": "AWS Team",
        "swqwd.scg.com": "AWS Team",
        "swpwd.scg.com": "AWS Team",
        "e-hr.scg.co.th": "AWS Team",
        "uat-e-hr.scg.co.th": "AWS Team",
        "dev-e-hr.scg.co.th": "AWS Team",
        "ehr.scg.co.th": "AWS Team",
        "uat-hr.scg.co.th": "AWS Team",
        "dev-hr.scg.co.th": "AWS Team",
        "ehr-efm.scg.co.th": "AWS Team",
        "uat-hr-efm.scg.co.th": "AWS Team",
        "dev-hr-efm.scg.co.th": "AWS Team",
        "sandeeuat.scg.com": "AWS Team",
        "sandee.scg.com": "AWS Team",
        "scgchem-ecbqa.scg.com": "AWS Team",
        "ssdmsg.scg.com": "AWS Team",
        "ssqmsg.scg.com": "AWS Team",
        "sspmsg.scg.com": "AWS Team",
        "scc-awss4wd71.scg.com": "AWS Team",
        "scc-awss4wd01.scg.com": "AWS Team",
    }

    AWS_KEYWORDS = [
        "[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB",
        "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT",
        "EKS", "ECS", "BEDROCK", "IAM",
    ]

    GCP_KEYWORDS = [
        "[GCP]", "GCP", "GCP PROJECT", "GOOGLE", "GOOGLE WORKSPACE",
        "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDRUN",
        "APPENGINE", "GCP USER", "GOOGLE SHEET", "WORKSPACE",
    ]

    TRAINING_CLOUD_SUBTEAM_DATASET_PATH = env_or_default(
        "TRAINING_CLOUD_SUBTEAM_DATASET_PATH",
        os.path.join(EXPORT_DIR, "ticket_training_cloud_sub_team.csv")
    )

    TRAINING_MAIN_TEAM_DATASET_PATH = env_or_default(
        "TRAINING_MAIN_TEAM_DATASET_PATH",
        os.path.join(EXPORT_DIR, "ticket_training_main_team.csv")
    )

    TRAINING_TARGET_COLUMN_CLOUD_SUBTEAM = env_or_default(
        "TRAINING_TARGET_COLUMN_CLOUD_SUBTEAM",
        "label_sub_team"
    )
    TRAINING_TARGET_COLUMN_MAIN_TEAM = env_or_default(
        "TRAINING_TARGET_COLUMN_MAIN_TEAM",
        "label_main_team"
    )

    BEST_TICKET_CLASSIFIER_MODEL_PATH = env_or_default(
        "BEST_TICKET_CLASSIFIER_MODEL_PATH",
        os.path.join(TRAIN_DIR, "best_ticket_classifier_model.pkl")
    )

    BEST_MAIN_TEAM_MODEL_PATH = env_or_default(
        "BEST_MAIN_TEAM_MODEL_PATH",
        os.path.join(TRAIN_DIR, "best_main_team_model.pkl")
    )

    ENSEMBLE_BUNDLE_PATH = env_or_default(
        "ENSEMBLE_BUNDLE_PATH",
        os.path.join(TRAIN_DIR, "ticket_ensemble_bundle.pkl")
    )

    MODEL_COMPARISON_REPORT_PATH = env_or_default(
        "MODEL_COMPARISON_REPORT_PATH",
        os.path.join(TRAIN_DIR, "model_comparison_results.csv")
    )
    MAIN_TEAM_MODEL_COMPARISON_REPORT_PATH = env_or_default(
        "MAIN_TEAM_MODEL_COMPARISON_REPORT_PATH",
        os.path.join(TRAIN_DIR, "main_team_model_comparison_results.csv")
    )

    FEATURE_IMPORTANCE_OUTPUT_PATH = env_or_default(
        "FEATURE_IMPORTANCE_OUTPUT_PATH",
        os.path.join(TRAIN_DIR, "feature_importance_top200.csv")
    )

    EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH = env_or_default(
        "EXPLAIN_FEATURE_IMPORTANCE_OUTPUT_PATH",
        os.path.join(TRAIN_DIR, "explain_feature_importance_top200.csv")
    )

    RULE_UNMATCHED_CASES_PATH = env_or_default(
        "RULE_UNMATCHED_CASES_PATH",
        os.path.join(TRAIN_DIR, "rule_unmatched_cases.csv")
    )

    ML_RANDOM_STATE = int(env_or_default("ML_RANDOM_STATE", 42))
    ML_TEST_SIZE = float(env_or_default("ML_TEST_SIZE", 0.2))
    ML_CONFIDENCE_THRESHOLD = float(env_or_default("ML_CONFIDENCE_THRESHOLD", 0.75))

    VALID_CLOUD_SUBTEAM_LABELS = env_or_default(
        "VALID_CLOUD_SUBTEAM_LABELS",
        "AWS Team,GCP Team"
    )

    EXTRA_AWS_KEYWORDS = [
        "FIREWALL REQUEST : AWS HUB",
        "PHASSAKORN SEENIL",
    ]

    EXTRA_GCP_KEYWORDS = [
        "FIREWALL REQUEST : GCP HUB",
        "GEMINI",
        "CLOUDFUNCTIONS",
        "CLOUD RUN",
        "SPOKE01",
        "SHAREDSERVICES-PRD-RG",
    ]