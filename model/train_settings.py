import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.config import Config


# =========================================================
# 1) GLOBAL CONFIG
# =========================================================
TEST_SIZE = Config.ML_TEST_SIZE
RANDOM_STATE = Config.ML_RANDOM_STATE
CONFIDENCE_THRESHOLD = Config.ML_CONFIDENCE_THRESHOLD

AWS_KEYWORDS = list(Config.AWS_KEYWORDS) + list(Config.EXTRA_AWS_KEYWORDS)
GCP_KEYWORDS = list(Config.GCP_KEYWORDS) + list(Config.EXTRA_GCP_KEYWORDS)
SYSTEM_MAPPING = getattr(Config, "SYSTEM_MAPPING", {})