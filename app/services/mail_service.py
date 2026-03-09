import imaplib, email
from datetime import datetime, timedelta
from app.config import Config
from app.utils.parser import clean_text, extract_ticket_info

processed_tasks = set()

def fetch_and_group_tasks():
    all_tasks_list = []
    ritm_groups = {}
    mail = None

    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=30) 
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        mail.select("scg")

        since_date = (datetime.now() - timedelta(days=31)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(SINCE "{since_date}")')
        ids = messages[0].split()

        if not ids: return []

        for m_id in reversed(ids):
            try:
                _, msg_data = mail.fetch(m_id, "(RFC822)")
                if not msg_data or not msg_data[0]: continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                date_str = msg.get("Date")
                msg_date = email.utils.parsedate_to_datetime(date_str)
                subject = msg.get("Subject", "")

                if Config.TARGET_SENDER not in msg.get("From", ""): continue

                to_address = msg.get("To", "").lower()
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            try: body += part.get_payload(decode=True).decode('utf-8', errors='replace')
                            except: pass
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

                clean_body = clean_text(body)
                info = extract_ticket_info(clean_body, subject)

                current_task_id = "N/A"
                display_parent_id = "N/A"
                display_short_desc = "N/A"

                if info["is_valid_itask"]:
                    current_task_id = info["itask_no"]
                    display_parent_id = info["itask_no"]
                    display_short_desc = info["inc_short_desc"]
                elif info["is_valid_ritm"]:
                    current_task_id = info["task_no"]
                    display_parent_id = info["ritm_no"]
                    display_short_desc = info["task_short_desc"]
                elif info["is_valid_ctask"]:
                    current_task_id = info["ctask_no"]
                    display_parent_id = info["ctask_no"]
                    display_short_desc = info["ctask_short_desc"]

                if current_task_id == "N/A" or current_task_id in processed_tasks:
                    continue

                # --- 2. Advanced Decision Matrix ---
                final_route = "GCP & AWS Team (Both)"
                assigned_team_key = None
                if "scg-wifi@inetms.co.th" in to_address:
                    assigned_team_key = "iNET Network Team"
                elif "scgcloud@inetms.co.th" in to_address:
                    assigned_team_key = "iNET Operation Team"
                elif "inetmscloud@inetms.co.th" in to_address:
                    assigned_team_key = "iNET Cloud Support Team"
                elif "scg_cloud_inet01@scg.com" in to_address:
                    assigned_team_key = "iNET Cloud Support Team"

                if assigned_team_key == "iNET Network Team":
                    final_route = "iNET Network Team"
                elif assigned_team_key == "iNET Operation Team":
                    final_route = "iNET Operation Team"
                elif assigned_team_key == "iNET Cloud Support Team":
                    full_content = clean_body.upper()
                    env_text = info["related_env"].upper()
                    task_header = info["task_short_desc"].upper()
                    ritm_header = info["ritm_short_desc"].upper()
                    ritm_desc = info["description"].upper()
                    found_team = False

                    # A. เช็คจาก IP
                    if info["ips"]:
                        if any("41" in ip for ip in info["ips"]): final_route = "AWS Team"; found_team = True
                        elif any("42" in ip for ip in info["ips"]): final_route = "GCP Team"; found_team = True

                    # B. Keyword Hierarchy
                    if not found_team:
                        combined_headers = (task_header + " " + ritm_header).upper()
    
                        is_header_gcp = any(k in combined_headers for k in ["[GCP]", "GCP", "GCP Project", "GOOGLE", "GEMINI", "GOOGLE WORKSPACE", "GCP USER", "GCP user", "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDFUNCTIONS", "CLOUDRUN", "APPENGINE", "Cloud Run", "spoke01", "sharedservices-prd-rg"])
                        is_header_aws = any(k in combined_headers for k in ["[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB", "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT", "ELB", "EKS", "ECS", "Phassakorn Seenil"])

                        if is_header_gcp and not is_header_aws:
                            final_route = "GCP Team"; found_team = True
                        elif is_header_aws and not is_header_gcp:
                            final_route = "AWS Team"; found_team = True
                        # is_header_gcp = any(k in task_header for k in ["[GCP]", "GCP", "GCP Project", "GOOGLE", "GEMINI", "GOOGLE WORKSPACE", "GCP USER", "GCP user", "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDFUNCTIONS", "CLOUDRUN", "APPENGINE", "Cloud Run", "spoke01", "sharedservices-prd-rg"])
                        # is_header_aws = any(k in task_header for k in ["[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB", "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT", "ELB", "EKS", "ECS", "Phassakorn Seenil"])
                        # if is_header_gcp and not is_header_aws: final_route = "GCP Team"; found_team = True
                        # elif is_header_aws and not is_header_gcp: final_route = "AWS Team"; found_team = True

                    if not found_team:
                        desc_has_gcp = any(k in full_content for k in ["GOOGLE", "GCP", "GEMINI", "GOOGLE WORKSPACE"])
                        desc_has_aws = any(k in full_content for k in ["AWS", "AMAZON", "AWS HUB"])
                        if (env_text.count("GCP") > 0 or desc_has_gcp) and not desc_has_aws: final_route = "GCP Team"; found_team = True
                        elif (env_text.count("AWS") > 0 or desc_has_aws) and not desc_has_gcp: final_route = "AWS Team"; found_team = True

                    if not found_team:
                        header_content = f"{subject} {ritm_header} {ritm_desc}"
                        is_header_gcp = any(k in header_content for k in ["[GCP]", "GCP", "GCP Project", "GOOGLE", "GEMINI", "GOOGLE WORKSPACE", "GCP USER", "GCP user", "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDFUNCTIONS", "CLOUDRUN", "APPENGINE", "Cloud Run", "spoke01", "sharedservices-prd-rg"])
                        is_header_aws = any(k in header_content for k in ["[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB", "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT", "ELB", "EKS", "ECS", "Phassakorn Seenil"])
                        if is_header_gcp and not is_header_aws: final_route = "GCP Team"; found_team = True
                        elif is_header_aws and not is_header_gcp: final_route = "AWS Team"; found_team = True

                    # C. เช็คจาก URL
                    if not found_team:
                        for url in info["urls"]:
                            for domain, team in Config.SYSTEM_MAPPING.items():
                                if domain in url.lower(): final_route = team; found_team = True; break
                            if found_team: break

                else:
                    continue

                # เก็บข้อมูลลงกลุ่ม RITM
                task_obj = {
                    "task": current_task_id,
                    "ritm": display_parent_id,
                    "short_desc": display_short_desc,
                    "env": info["related_env"],
                    "final_route": final_route,
                    "sent_date": msg_date
                }
                
                if display_parent_id not in ritm_groups:
                    ritm_groups[display_parent_id] = []
                ritm_groups[display_parent_id].append(task_obj)
                processed_tasks.add(current_task_id)

            except Exception as e:
                print(f"❌ Error processing message: {e}")

        # --- [จุดแก้ไขสำคัญ] Cross-Task Logic ภายใต้ RITM เดียวกัน ---
        for ritm_id, tasks in ritm_groups.items():
            if len(tasks) > 1:
                # 1. หาดูว่ามี Task ไหนใน RITM นี้ที่รู้ทีมชัดเจนแล้วหรือไม่ (ไม่ใช่ "Both")
                known_team = None
                for t in tasks:
                    if t["final_route"] in ["GCP Team", "AWS Team"]:
                        known_team = t["final_route"]
                        break
                
                # 2. ถ้ามีหนึ่ง Task รู้ทีมแล้ว และอีก Task ยังเป็น "Both"
                # ให้สลับ Task ที่เป็น Both ไปให้อีกทีมตามเงื่อนไข (GCP Hub <-> AWS Hub)
                if known_team:
                    for t in tasks:
                        if t["final_route"] == "GCP & AWS Team (Both)":
                            if known_team == "GCP Team":
                                t["final_route"] = "AWS Team"
                            else:
                                t["final_route"] = "GCP Team"

            # นำ Task ที่ประมวลผล Cross-Check แล้วใส่ลงรายการสรุป
            all_tasks_list.extend(tasks)

        all_tasks_list.sort(key=lambda x: x["sent_date"])
        mail.logout()

    except Exception as e:
        print(f"📧 IMAP Error: {e}")
    finally:
        if mail:
            try: mail.close()
            except: pass

    return all_tasks_list

# TODO ---------------------------------------------------------- new

# import imaplib
# import email
# import os
# import math
# from datetime import datetime, timedelta
# from email.header import decode_header

# import joblib

# from app.config import Config
# from app.utils.parser import clean_text, extract_ticket_info
# from app.utils.ml_utils import thai_tokenizer  # สำคัญ: ต้อง import ก่อน load model


# # =========================================================
# # 1) CONFIG
# # =========================================================
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# PROJECT_ROOT = os.path.dirname(BASE_DIR)

# MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "best_ticket_classifier_model.pkl")

# ML_CONFIDENCE_THRESHOLD = 0.75
# IMAP_TIMEOUT = 30
# MAILBOX_FOLDER = "scg"
# DAYS_BACK = 2

# AWS_ROUTE = "AWS Team"
# GCP_ROUTE = "GCP Team"
# BOTH_ROUTE = "GCP & AWS Team (Both)"
# KNOWN_CLOUD_ROUTES = {AWS_ROUTE, GCP_ROUTE}

# processed_tasks = set()


# # =========================================================
# # 2) LOAD MODEL
# # =========================================================
# try:
#     ml_model = joblib.load(MODEL_PATH)
#     print(f"✅ ML Model loaded successfully: {MODEL_PATH}")
# except Exception as e:
#     print(f"⚠️ Warning: Could not load ML model: {e}")
#     ml_model = None


# # =========================================================
# # 3) GENERIC HELPERS
# # =========================================================
# def decode_mime_words(text):
#     if not text:
#         return ""

#     decoded_parts = decode_header(text)
#     result = []

#     for part, enc in decoded_parts:
#         if isinstance(part, bytes):
#             try:
#                 result.append(part.decode(enc or "utf-8", errors="replace"))
#             except Exception:
#                 result.append(part.decode("utf-8", errors="replace"))
#         else:
#             result.append(part)

#     return "".join(result)


# def normalize_text(value):
#     if not value:
#         return ""
#     return " ".join(str(value).replace("\r", " ").replace("\n", " ").split()).strip()


# def softmax(values):
#     if not values:
#         return []

#     max_val = max(values)
#     exps = [math.exp(v - max_val) for v in values]
#     total = sum(exps)

#     if total == 0:
#         return [0.0 for _ in values]

#     return [v / total for v in exps]


# def get_opposite_route(route: str) -> str:
#     if route == AWS_ROUTE:
#         return GCP_ROUTE
#     if route == GCP_ROUTE:
#         return AWS_ROUTE
#     return BOTH_ROUTE


# def env_has_aws(text: str) -> bool:
#     text = normalize_text(text).upper()
#     return "AWS" in text or "AMAZON" in text


# def env_has_gcp(text: str) -> bool:
#     text = normalize_text(text).upper()
#     return "GCP" in text or "GOOGLE" in text


# def env_has_both_clouds(text: str) -> bool:
#     return env_has_aws(text) and env_has_gcp(text)


# # =========================================================
# # 4) SUBJECT / TASK HELPERS
# # =========================================================
# def is_valid_assignment_subject(subject: str) -> bool:
#     """
#     รับเฉพาะ:
#     - Catalog Task ... has been assigned ...
#     - Incident task ... has been assigned ...
#     - Change task ... has been assigned ...
#     """
#     subject = normalize_text(subject).lower()

#     valid_patterns = [
#         "catalog task" in subject and "has been assigned" in subject,
#         "incident task" in subject and "has been assigned" in subject,
#         "change task" in subject and "has been assigned" in subject,
#     ]
#     return any(valid_patterns)


# def get_ticket_type(info):
#     if info.get("is_valid_itask"):
#         return "incident_task"
#     if info.get("is_valid_ritm"):
#         return "catalog_task"
#     if info.get("is_valid_ctask"):
#         return "change_task"
#     return "unknown"


# def determine_task_identity(info):
#     current_task_id = "N/A"
#     display_parent_id = "N/A"
#     display_short_desc = "N/A"
#     ticket_type = get_ticket_type(info)

#     if info.get("is_valid_itask"):
#         current_task_id = info.get("itask_no", "N/A")
#         display_parent_id = info.get("itask_no", "N/A")
#         display_short_desc = info.get("inc_short_desc", "N/A")

#     elif info.get("is_valid_ritm"):
#         current_task_id = info.get("task_no", "N/A")
#         display_parent_id = info.get("ritm_no", "N/A")
#         display_short_desc = info.get("task_short_desc", "N/A")

#     elif info.get("is_valid_ctask"):
#         current_task_id = info.get("ctask_no", "N/A")
#         display_parent_id = info.get("ctask_no", "N/A")
#         display_short_desc = info.get("ctask_short_desc", "N/A")

#     return ticket_type, current_task_id, display_parent_id, display_short_desc


# def detect_assigned_team_by_to(to_address: str):
#     to_address = normalize_text(to_address).lower()

#     if "scg-wifi@inetms.co.th" in to_address:
#         return "iNET Network Team"
#     if "scgcloud@inetms.co.th" in to_address:
#         return "iNET Operation Team"
#     if "inetmscloud@inetms.co.th" in to_address:
#         return "iNET Cloud Support Team"
#     if "scg_cloud_inet01@scg.com" in to_address:
#         return "iNET Cloud Support Team"
#     return None


# # =========================================================
# # 5) ML HELPERS
# # =========================================================
# def build_ml_text(ticket_type, to_address, subject, short_desc, ritm_desc, description, env, body_text):
#     parts = [
#         f"ticket_type: {normalize_text(ticket_type)}",
#         f"to_address: {normalize_text(to_address)}",
#         f"subject: {normalize_text(subject)}",
#         f"task_short_desc: {normalize_text(short_desc)}",
#         f"ritm_short_desc: {normalize_text(ritm_desc)}",
#         f"description: {normalize_text(description)}",
#         f"related_env: {normalize_text(env)}",
#         f"body_text: {normalize_text(body_text)}",
#     ]
#     return " ||| ".join([p for p in parts if p.strip()])

# def predict_router(ticket_type, to_address, subject, short_desc, ritm_desc, description, env, body_text):
#     """
#     Return:
#         predicted_team: str | None
#         confidence: float
#         ml_text: str
#     """
#     ml_text = build_ml_text(
#         ticket_type=ticket_type,
#         to_address=to_address,
#         subject=subject,
#         short_desc=short_desc,
#         ritm_desc=ritm_desc,
#         description=description,
#         env=env,
#         body_text=body_text,
#     )

#     if not ml_model:
#         return None, 0.0, ml_text

#     try:
#         if not ml_text.strip():
#             return None, 0.0, ml_text

#         prediction = ml_model.predict([ml_text])[0]
#         confidence = 0.0

#         if hasattr(ml_model, "predict_proba"):
#             probs = ml_model.predict_proba([ml_text])[0]
#             confidence = float(max(probs))

#         elif hasattr(ml_model, "decision_function"):
#             scores = ml_model.decision_function([ml_text])
#             if hasattr(scores, "__len__") and len(scores) > 0:
#                 row = scores[0] if hasattr(scores[0], "__len__") else scores
#                 row = [float(x) for x in row]
#                 probs = softmax(row)
#                 confidence = float(max(probs))

#         return str(prediction), confidence, ml_text

#     except Exception as e:
#         print(f"❌ ML Prediction Error: {e}")
#         return None, 0.0, ml_text


# # =========================================================
# # 6) RULE-BASED CLOUD ROUTER
# # =========================================================
# def route_by_rules(info, clean_body, subject=""):
#     final_route = BOTH_ROUTE
#     found_team = False

#     full_text = f"{subject} {clean_body}".upper()

#     if "[GCP]" in full_text:
#         return GCP_ROUTE

#     if "[AWS]" in full_text:
#         return AWS_ROUTE

#     full_content = normalize_text(clean_body).upper()
#     env_text = normalize_text(info.get("related_env", "")).upper()
#     task_header = normalize_text(info.get("task_short_desc", "")).upper()
#     ritm_header = normalize_text(info.get("ritm_short_desc", "")).upper()
#     ritm_desc = normalize_text(info.get("description", "")).upper()

#     ips = info.get("ips", []) or []
#     urls = info.get("urls", []) or []

#     # A. IP
#     if ips:
#         if any(str(ip).startswith("10.41.") for ip in ips):
#             final_route = AWS_ROUTE
#             found_team = True
#         elif any(str(ip).startswith("10.42.") for ip in ips):
#             final_route = GCP_ROUTE
#             found_team = True

#     # B. Header keywords
#     if not found_team:
#         subject_text = normalize_text(subject).upper()
#         combined_headers = f"{subject_text} {task_header} {ritm_header}"
#         is_header_gcp = any(k in combined_headers for k in ["[GCP]", "GCP", "GCP Project", "GOOGLE", "GEMINI", "GOOGLE WORKSPACE", "GCP USER", "GCP user", "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDFUNCTIONS", "CLOUDRUN", "APPENGINE", "Cloud Run", "spoke01", "sharedservices-prd-rg"])
#         is_header_aws = any(k in combined_headers for k in ["[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB", "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT", "ELB", "EKS", "ECS", "Phassakorn Seenil"])

#         if is_header_gcp and not is_header_aws:
#             final_route = GCP_ROUTE
#             found_team = True
#         elif is_header_aws and not is_header_gcp:
#             final_route = AWS_ROUTE
#             found_team = True

#     # C1. Related environment แบบ strict
#     if not found_team:
#         has_gcp = env_has_gcp(env_text)
#         has_aws = env_has_aws(env_text)

#         if has_gcp and not has_aws:
#             final_route = GCP_ROUTE
#             found_team = True
#         elif has_aws and not has_gcp:
#             final_route = AWS_ROUTE
#             found_team = True

#     # C2. Body keywords
#     if not found_team:
#         desc_has_gcp = any(k in full_content for k in ["[GCP]", " GCP ", "GCP HUB", "CLOUD - GCP"])
#         desc_has_aws = any(k in full_content for k in ["[AWS]", " AWS ", "AWS HUB", "CLOUD - AWS"])

#         if desc_has_gcp and not desc_has_aws:
#             final_route = GCP_ROUTE
#             found_team = True
#         elif desc_has_aws and not desc_has_gcp:
#             final_route = AWS_ROUTE
#             found_team = True

#     # D. Description fallback
#     if not found_team:
#         header_content = f"{subject_text} {ritm_header} {ritm_desc}"
#         is_header_gcp = any(k in header_content for k in ["[GCP]", "GCP", "GCP Project", "GOOGLE", "GEMINI", "GOOGLE WORKSPACE", "GCP USER", "GCP user", "GOOGLE CLOUD", "GKE", "GCS", "BIGQUERY", "CLOUDFUNCTIONS", "CLOUDRUN", "APPENGINE", "Cloud Run", "spoke01", "sharedservices-prd-rg"])
#         is_header_aws = any(k in header_content for k in ["[AWS]", "AWS", "AMAZON", "AWS HUB", "EC2", "ALB", "NLB", "ELB", "ACM", "ROUTE 53", "WAF", "S3", "RDS", "LAMBDA", "CLOUDFRONT", "ELB", "EKS", "ECS", "Phassakorn Seenil"])

#         if is_header_gcp and not is_header_aws:
#             final_route = GCP_ROUTE
#             found_team = True
#         elif is_header_aws and not is_header_gcp:
#             final_route = AWS_ROUTE
#             found_team = True

#     # E. URL
#     if not found_team:
#         for url in urls:
#             url_lower = str(url).lower()
#             for domain, team in Config.SYSTEM_MAPPING.items():
#                 if domain.lower() in url_lower:
#                     final_route = team
#                     found_team = True
#                     break
#             if found_team:
#                 break

#     return final_route


# # =========================================================
# # 7) RESOLVERS
# # =========================================================
# def resolve_single_cloud_task(task):
#     """
#     ถ้าเป็น cloud task เดี่ยว:
#     - ถ้าชัด AWS/GCP คงไว้
#     - ถ้าไม่ชัด -> Both
#     """
#     route = task.get("final_route", BOTH_ROUTE)
#     confidence = float(task.get("ml_confidence", 0.0) or 0.0)
#     prediction_source = task.get("prediction_source", "")

#     if route in KNOWN_CLOUD_ROUTES:
#         return task

#     if prediction_source == "ML" and confidence >= ML_CONFIDENCE_THRESHOLD:
#         if task.get("ml_prediction") in KNOWN_CLOUD_ROUTES:
#             task["final_route"] = task["ml_prediction"]
#             return task

#     task["final_route"] = BOTH_ROUTE
#     return task


# def resolve_cloud_group_tasks(ritm_id, tasks):
#     """
#     กติกา:
#     - พิจารณาเฉพาะกลุ่ม iNET Cloud Support Team
#     - ถ้ามี 2 task และ env รวมมีทั้ง AWS + GCP
#         - ถ้า task หนึ่งชัด -> อีก task เป็นอีกทีม
#         - ถ้าทั้งคู่ชัดและคนละทีมอยู่แล้ว -> คงเดิม
#         - ถ้าทั้งคู่ชัดแต่เป็นทีมเดียวกัน -> เก็บตัวที่มั่นใจกว่า แล้วอีกตัวเป็นอีกทีม
#         - ถ้ายังไม่ชัดจริง ๆ -> Both
#     - ถ้าไม่เข้าเงื่อนไขด้านบน:
#         - แต่ละ task ถ้าไม่ชัด -> Both
#     """
#     if not tasks:
#         return tasks

#     cloud_tasks = [t for t in tasks if t.get("assigned_team_key") == "iNET Cloud Support Team"]
#     non_cloud_tasks = [t for t in tasks if t.get("assigned_team_key") != "iNET Cloud Support Team"]

#     for t in non_cloud_tasks:
#         if not t.get("final_route"):
#             t["final_route"] = t.get("assigned_team_key", t.get("final_route"))

#     if not cloud_tasks:
#         return tasks

#     if len(cloud_tasks) != 2:
#         for t in cloud_tasks:
#             resolve_single_cloud_task(t)
#         return tasks

#     combined_env = " ".join(normalize_text(t.get("env", "")) for t in cloud_tasks)

#     if not env_has_both_clouds(combined_env):
#         for t in cloud_tasks:
#             resolve_single_cloud_task(t)
#         return tasks

#     t1, t2 = cloud_tasks[0], cloud_tasks[1]

#     r1 = t1.get("final_route", BOTH_ROUTE)
#     r2 = t2.get("final_route", BOTH_ROUTE)

#     c1 = float(t1.get("ml_confidence", 0.0) or 0.0)
#     c2 = float(t2.get("ml_confidence", 0.0) or 0.0)

#     clear1 = r1 in KNOWN_CLOUD_ROUTES
#     clear2 = r2 in KNOWN_CLOUD_ROUTES

#     # 1) ทั้งคู่ชัดและคนละทีมอยู่แล้ว
#     if clear1 and clear2 and {r1, r2} == {AWS_ROUTE, GCP_ROUTE}:
#         print(f"🔀 RITM_RESOLVER | RITM={ritm_id} | Already split correctly -> {t1['task']}={r1}, {t2['task']}={r2}")
#         return tasks

#     # 2) อันหนึ่งชัด อีกอันไม่ชัด
#     if clear1 and not clear2:
#         t2["final_route"] = get_opposite_route(r1)
#         t2["prediction_source"] = "RITM_RESOLVER"
#         print(f"🔀 RITM_RESOLVER | RITM={ritm_id} | {t1['task']}={r1} clear, force {t2['task']}={t2['final_route']}")
#         return tasks

#     if clear2 and not clear1:
#         t1["final_route"] = get_opposite_route(r2)
#         t1["prediction_source"] = "RITM_RESOLVER"
#         print(f"🔀 RITM_RESOLVER | RITM={ritm_id} | {t2['task']}={r2} clear, force {t1['task']}={t1['final_route']}")
#         return tasks

#     # 3) ทั้งคู่ชัด แต่ชี้ทีมเดียวกัน
#     if clear1 and clear2 and r1 == r2:
#         if c1 >= c2:
#             t2["final_route"] = get_opposite_route(r1)
#             t2["prediction_source"] = "RITM_RESOLVER"
#             print(
#                 f"🔀 RITM_RESOLVER | RITM={ritm_id} | same={r1}, keep {t1['task']} ({c1:.2%}), "
#                 f"flip {t2['task']} -> {t2['final_route']}"
#             )
#         else:
#             t1["final_route"] = get_opposite_route(r2)
#             t1["prediction_source"] = "RITM_RESOLVER"
#             print(
#                 f"🔀 RITM_RESOLVER | RITM={ritm_id} | same={r2}, keep {t2['task']} ({c2:.2%}), "
#                 f"flip {t1['task']} -> {t1['final_route']}"
#             )
#         return tasks

#     # 4) ยังไม่ชัดจริง ๆ
#     t1["final_route"] = BOTH_ROUTE
#     t2["final_route"] = BOTH_ROUTE
#     t1["prediction_source"] = "RITM_BOTH"
#     t2["prediction_source"] = "RITM_BOTH"
#     print(f"🔀 RITM_RESOLVER | RITM={ritm_id} | unresolved -> BOTH for {t1['task']}, {t2['task']}")
#     return tasks


# # =========================================================
# # 8) EMAIL BODY HELPER
# # =========================================================
# def extract_email_body(msg):
#     body = ""

#     if msg.is_multipart():
#         for part in msg.walk():
#             if part.get_content_type() in ["text/plain", "text/html"]:
#                 try:
#                     payload = part.get_payload(decode=True)
#                     if payload:
#                         body += payload.decode("utf-8", errors="replace")
#                 except Exception:
#                     pass
#     else:
#         try:
#             payload = msg.get_payload(decode=True)
#             if payload:
#                 body = payload.decode("utf-8", errors="replace")
#         except Exception:
#             body = ""

#     return body


# # =========================================================
# # 9) MAIN FETCH FUNCTION
# # =========================================================
# def fetch_and_group_tasks():
#     all_tasks_list = []
#     ritm_groups = {}
#     mail = None

#     debug_counts = {
#         "total_fetched": 0,
#         "skip_sender": 0,
#         "skip_subject": 0,
#         "skip_invalid_task": 0,
#         "skip_duplicate": 0,
#         "skip_to_address": 0,
#         "accepted": 0,
#         "ml_used": 0,
#         "rule_used": 0,
#         "both_used": 0,
#     }

#     try:
#         mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=IMAP_TIMEOUT)
#         mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)

#         select_status, _ = mail.select(MAILBOX_FOLDER)
#         if select_status != "OK":
#             print(f"❌ Cannot select mailbox: {MAILBOX_FOLDER}")
#             return []

#         since_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%d-%b-%Y")

#         status, messages = mail.search(None, f'(SINCE "{since_date}")')
#         if status != "OK":
#             print("📧 IMAP Search Error")
#             return []

#         ids = messages[0].split()
#         print(f"📨 Found {len(ids)} emails since {since_date}")

#         if not ids:
#             return []

#         for m_id in reversed(ids):
#             try:
#                 status, msg_data = mail.fetch(m_id, "(RFC822)")
#                 if status != "OK" or not msg_data or not msg_data[0]:
#                     continue

#                 debug_counts["total_fetched"] += 1

#                 msg = email.message_from_bytes(msg_data[0][1])

#                 date_str = msg.get("Date")
#                 msg_date = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()

#                 subject = decode_mime_words(msg.get("Subject", ""))
#                 from_address = decode_mime_words(msg.get("From", ""))
#                 to_address = decode_mime_words(msg.get("To", "")).lower()

#                 if Config.TARGET_SENDER.lower() not in from_address.lower():
#                     debug_counts["skip_sender"] += 1
#                     continue

#                 if not is_valid_assignment_subject(subject):
#                     debug_counts["skip_subject"] += 1
#                     continue

#                 body = extract_email_body(msg)
#                 clean_body = clean_text(body)
#                 info = extract_ticket_info(clean_body, subject)

#                 ticket_type, current_task_id, display_parent_id, display_short_desc = determine_task_identity(info)

#                 if current_task_id == "N/A":
#                     debug_counts["skip_invalid_task"] += 1
#                     continue

#                 if current_task_id in processed_tasks:
#                     debug_counts["skip_duplicate"] += 1
#                     continue

#                 assigned_team_key = detect_assigned_team_by_to(to_address)
#                 if not assigned_team_key:
#                     debug_counts["skip_to_address"] += 1
#                     print(
#                         f"⏭️ SKIP TO_ADDRESS | Task={current_task_id} | Parent={display_parent_id} | Subject={subject} | To={to_address}"
#                     )
#                     continue

#                 debug_counts["accepted"] += 1

#                 final_route = BOTH_ROUTE
#                 prediction_source = "RULE"
#                 ml_confidence = 0.0
#                 ml_prediction = None

#                 # Main team direct route
#                 if assigned_team_key == "iNET Network Team":
#                     final_route = "iNET Network Team"
#                     prediction_source = "RULE_MAIN_TEAM"

#                 elif assigned_team_key == "iNET Operation Team":
#                     final_route = "iNET Operation Team"
#                     prediction_source = "RULE_MAIN_TEAM"

#                 elif assigned_team_key == "iNET Cloud Support Team":
#                     ml_prediction, ml_confidence, _ = predict_router(
#                         ticket_type=ticket_type,
#                         to_address=to_address,
#                         subject=subject,
#                         short_desc=display_short_desc,
#                         ritm_desc=info.get("ritm_short_desc", ""),
#                         description=info.get("description", ""),
#                         env=info.get("related_env", ""),
#                         body_text=clean_body,
#                     )

#                     if ml_prediction:
#                         print(
#                             f"🤖 ML_CHECK | Task={current_task_id} | Pred={ml_prediction} "
#                             f"| Confidence={ml_confidence:.2%}"
#                         )

#                     if ml_prediction in KNOWN_CLOUD_ROUTES and ml_confidence >= ML_CONFIDENCE_THRESHOLD:
#                         final_route = ml_prediction
#                         prediction_source = "ML"
#                         debug_counts["ml_used"] += 1

#                         print(
#                             f"🤖 ML_ROUTER | Task={current_task_id} | Final={final_route} "
#                             f"| Confidence={ml_confidence:.2%}"
#                         )
#                     else:
#                         final_route = route_by_rules(info, clean_body, subject)

#                         if final_route in KNOWN_CLOUD_ROUTES:
#                             prediction_source = "RULE_FALLBACK"
#                             debug_counts["rule_used"] += 1
#                         else:
#                             prediction_source = "UNRESOLVED"
#                             debug_counts["both_used"] += 1

#                         print(
#                             f"⚠️ RULE_FALLBACK | Task={current_task_id} | ML={ml_prediction} "
#                             f"| Confidence={ml_confidence:.2%} | Final={final_route}"
#                         )

#                 task_obj = {
#                     "task": current_task_id,
#                     "ritm": display_parent_id,
#                     "ticket_type": ticket_type,
#                     "short_desc": display_short_desc,
#                     "description": info.get("description", ""),
#                     "env": info.get("related_env", ""),
#                     "final_route": final_route,
#                     "sent_date": msg_date,
#                     "assigned_team_key": assigned_team_key,
#                     "prediction_source": prediction_source,
#                     "ml_prediction": ml_prediction,
#                     "ml_confidence": ml_confidence,
#                     "subject": subject,
#                 }

#                 if display_parent_id not in ritm_groups:
#                     ritm_groups[display_parent_id] = []

#                 ritm_groups[display_parent_id].append(task_obj)
#                 processed_tasks.add(current_task_id)

#             except Exception as e:
#                 print(f"❌ Error processing message: {e}")

#         for ritm_id, tasks in ritm_groups.items():
#             resolved_tasks = resolve_cloud_group_tasks(ritm_id, tasks)
#             all_tasks_list.extend(resolved_tasks)

#         all_tasks_list.sort(key=lambda x: x["sent_date"])

#         print("📊 Debug summary:", debug_counts)

#         for task in all_tasks_list:
#             print(
#                 f"📌 FINAL | Task={task['task']} | Parent={task['ritm']} | "
#                 f"Route={task['final_route']} | Source={task['prediction_source']} | "
#                 f"ML={task.get('ml_prediction')} | Confidence={float(task.get('ml_confidence', 0.0)):.2%}"
#             )

#         try:
#             mail.logout()
#         except Exception:
#             pass

#     except Exception as e:
#         print(f"📧 IMAP Error: {e}")

#     finally:
#         if mail:
#             try:
#                 mail.close()
#             except Exception:
#                 pass

#     return all_tasks_list