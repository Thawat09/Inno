import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    IMAP_SERVER = os.getenv("IMAP_SERVER")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
    LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))
    
    TARGET_SENDER = "SCGTicketSystems@service-now.com"
    TARGET_RECEIVER = {
        "scg-wifi@inetms.co.th": "iNET Network Team",
        "scgcloud@inetms.co.th": "iNET Operation Team",
        "inetmscloud@inetms.co.th": "iNET Cloud Support Team"
    }

    # สำหรับดักจับเคส Incident ผ่าน URL
    SYSTEM_MAPPING = {
        "justperformqas.scg.com": "AWS Team",
        "api-justperformqas.scg.com": "AWS Team",
        "tscpcl.outsystemsenterprise.com": "AWS Team",
        "aws": "AWS Team",
        "gcp": "GCP Team",
        "google": "GCP Team"
    }