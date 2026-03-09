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
        "inetmscloud@inetms.co.th": "iNET Cloud Support Team",
        "scg_cloud_inet01@scg.com": "iNET Cloud Support Team"
    }

    # สำหรับดักจับเคส Incident ผ่าน URL
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
        "scc-awss4wd01.scg.com": "AWS Team"
    }