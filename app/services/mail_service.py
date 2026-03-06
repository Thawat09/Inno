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

        since_date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
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

                    # B. เช็คจาก URL
                    if not found_team:
                        for url in info["urls"]:
                            for domain, team in Config.SYSTEM_MAPPING.items():
                                if domain in url.lower(): final_route = team; found_team = True; break
                            if found_team: break

                    # C. Keyword Hierarchy
                    if not found_team:
                        combined_headers = (task_header + " " + ritm_header).upper()
    
                        is_header_gcp = any(k in combined_headers for k in ["[GCP]", "GCP", "GOOGLE"])
                        is_header_aws = any(k in combined_headers for k in ["[AWS]", "AWS", "AMAZON"])

                        if is_header_gcp and not is_header_aws:
                            final_route = "GCP Team"; found_team = True
                        elif is_header_aws and not is_header_gcp:
                            final_route = "AWS Team"; found_team = True
                        # is_header_gcp = any(k in task_header for k in ["[GCP]", "GOOGLE", "GCP", "CLOUD - GCP"])
                        # is_header_aws = any(k in task_header for k in ["[AWS]", "AMAZON", "AWS", "CLOUD - AWS"])
                        # if is_header_gcp and not is_header_aws: final_route = "GCP Team"; found_team = True
                        # elif is_header_aws and not is_header_gcp: final_route = "AWS Team"; found_team = True

                    if not found_team:
                        desc_has_gcp = any(k in full_content for k in ["GOOGLE", "GCP", "GEMINI", "GOOGLE WORKSPACE"])
                        desc_has_aws = any(k in full_content for k in ["AWS", "AMAZON", "AWS HUB"])
                        if (env_text.count("GCP") > 0 or desc_has_gcp) and not desc_has_aws: final_route = "GCP Team"; found_team = True
                        elif (env_text.count("AWS") > 0 or desc_has_aws) and not desc_has_gcp: final_route = "AWS Team"; found_team = True

                    if not found_team:
                        header_content = ritm_header + " " + ritm_desc
                        is_header_gcp = any(k in header_content for k in ["[GCP]", "GOOGLE", "GCP"])
                        is_header_aws = any(k in header_content for k in ["[AWS]", "AMAZON", "AWS"])
                        if is_header_gcp and not is_header_aws: final_route = "GCP Team"; found_team = True
                        elif is_header_aws and not is_header_gcp: final_route = "AWS Team"; found_team = True

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

# TODO ---------------------------------------------------------- new version model
#! Flow การทำงานที่หายไป คือ หากมี 2 task แล้วตรง relate บอกแล้วว่าต้องมีทั้ง GCP และ AWS แล้วรู้แล้วว่า task นึงเป็น GCP อีก task นึงต้องให้เป็น AWS เลย ถ้าแก้ตรงนี้ได้น่าจะสมบูรณ์มากขึ้น แล้วลบของเก่าออกไปได้เลย

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
# DAYS_BACK = 30


# # =========================================================
# # 2) LOAD MODEL
# # =========================================================
# try:
#     ml_model = joblib.load(MODEL_PATH)
#     print("✅ ML Model loaded successfully.")
# except Exception as e:
#     print(f"⚠️ Warning: Could not load ML model: {e}")
#     ml_model = None


# processed_tasks = set()


# # =========================================================
# # 3) HELPERS
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
#     return str(value).replace("\r", " ").replace("\n", " ").strip()


# def softmax(values):
#     if not values:
#         return []
#     max_val = max(values)
#     exps = [math.exp(v - max_val) for v in values]
#     total = sum(exps)
#     if total == 0:
#         return [0.0 for _ in values]
#     return [v / total for v in exps]


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


# # =========================================================
# # 4) BUILD ML TEXT
# # ต้องให้ใกล้กับ format ตอน train model มากที่สุด
# # =========================================================
# def build_ml_text(ticket_type, to_address, short_desc, ritm_desc, description, env, body_text):
#     return (
#         "TICKET_TYPE: " + normalize_text(ticket_type) + " ||| " +
#         "TO_ADDRESS: " + normalize_text(to_address) + " ||| " +
#         "SUBJECT: " + normalize_text(short_desc) + " ||| " +
#         "TASK_DESC: " + normalize_text(short_desc) + " ||| " +
#         "RITM_DESC: " + normalize_text(ritm_desc) + " ||| " +
#         "DETAIL: " + normalize_text(description) + " ||| " +
#         "ENV: " + normalize_text(env) + " ||| " +
#         "BODY: " + normalize_text(body_text)
#     )


# # =========================================================
# # 5) PREDICT ROUTER
# # =========================================================
# def predict_router(ticket_type, to_address, short_desc, ritm_desc, description, env, body_text):
#     """
#     Return:
#         predicted_team: str | None
#         confidence: float
#         ml_text: str
#     """
#     ml_text = build_ml_text(
#         ticket_type=ticket_type,
#         to_address=to_address,
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

#         # For LogisticRegression / MultinomialNB
#         if hasattr(ml_model, "predict_proba"):
#             probs = ml_model.predict_proba([ml_text])[0]
#             confidence = float(max(probs))

#         # For LinearSVC
#         elif hasattr(ml_model, "decision_function"):
#             scores = ml_model.decision_function([ml_text])

#             # multiclass -> array of scores
#             if hasattr(scores, "__len__") and len(scores) > 0:
#                 row = scores[0] if hasattr(scores[0], "__len__") else scores
#                 row = [float(x) for x in row]
#                 probs = softmax(row)
#                 confidence = float(max(probs))
#             else:
#                 confidence = 0.0

#         return str(prediction), confidence, ml_text

#     except Exception as e:
#         print(f"❌ ML Prediction Error: {e}")
#         return None, 0.0, ml_text


# # =========================================================
# # 6) RULE-BASED ROUTER
# # =========================================================
# def route_by_rules(info, clean_body):
#     final_route = "GCP & AWS Team (Both)"
#     found_team = False

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
#             final_route = "AWS Team"
#             found_team = True
#         elif any(str(ip).startswith("10.42.") for ip in ips):
#             final_route = "GCP Team"
#             found_team = True

#     # B. URL
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

#     # C. Header keywords
#     if not found_team:
#         combined_headers = f"{task_header} {ritm_header}"
#         is_header_gcp = any(k in combined_headers for k in ["[GCP]", "GCP", "GOOGLE"])
#         is_header_aws = any(k in combined_headers for k in ["[AWS]", "AWS", "AMAZON"])

#         if is_header_gcp and not is_header_aws:
#             final_route = "GCP Team"
#             found_team = True
#         elif is_header_aws and not is_header_gcp:
#             final_route = "AWS Team"
#             found_team = True

#     # D. Body/env keywords
#     if not found_team:
#         desc_has_gcp = any(k in full_content for k in ["GOOGLE", "GCP", "GEMINI", "GOOGLE WORKSPACE"])
#         desc_has_aws = any(k in full_content for k in ["AWS", "AMAZON", "AWS HUB"])

#         if (env_text.count("GCP") > 0 or desc_has_gcp) and not desc_has_aws:
#             final_route = "GCP Team"
#             found_team = True
#         elif (env_text.count("AWS") > 0 or desc_has_aws) and not desc_has_gcp:
#             final_route = "AWS Team"
#             found_team = True

#     # E. Description fallback
#     if not found_team:
#         header_content = f"{ritm_header} {ritm_desc}"
#         is_header_gcp = any(k in header_content for k in ["[GCP]", "GOOGLE", "GCP"])
#         is_header_aws = any(k in header_content for k in ["[AWS]", "AMAZON", "AWS"])

#         if is_header_gcp and not is_header_aws:
#             final_route = "GCP Team"
#             found_team = True
#         elif is_header_aws and not is_header_gcp:
#             final_route = "AWS Team"
#             found_team = True

#     return final_route


# # =========================================================
# # 7) MAIN FETCH FUNCTION
# # =========================================================
# def fetch_and_group_tasks():
#     all_tasks_list = []
#     ritm_groups = {}
#     mail = None

#     try:
#         mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=IMAP_TIMEOUT)
#         mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
#         mail.select(MAILBOX_FOLDER)

#         since_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%d-%b-%Y")

#         # ค้นจาก sender ตั้งแต่ต้น จะเร็วกว่า
#         status, messages = mail.search(
#             None,
#             f'(SINCE "{since_date}" FROM "{Config.TARGET_SENDER}")'
#         )

#         if status != "OK":
#             print("📧 IMAP Search Error")
#             return []

#         ids = messages[0].split()
#         if not ids:
#             return []

#         total_ids = len(ids)

#         for idx, m_id in enumerate(reversed(ids), start=1):
#             try:
#                 printable_id = m_id.decode() if isinstance(m_id, bytes) else str(m_id)
#                 # print(f"📨 Fetching email {idx}/{total_ids} | ID={printable_id}")

#                 status, msg_data = mail.fetch(m_id, "(RFC822)")
#                 if status != "OK" or not msg_data or not msg_data[0]:
#                     continue

#                 msg = email.message_from_bytes(msg_data[0][1])

#                 date_str = msg.get("Date")
#                 msg_date = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()

#                 subject = decode_mime_words(msg.get("Subject", ""))
#                 from_address = decode_mime_words(msg.get("From", ""))
#                 to_address = decode_mime_words(msg.get("To", "")).lower()

#                 if Config.TARGET_SENDER.lower() not in from_address.lower():
#                     continue

#                 body = ""
#                 if msg.is_multipart():
#                     for part in msg.walk():
#                         if part.get_content_type() in ["text/plain", "text/html"]:
#                             try:
#                                 payload = part.get_payload(decode=True)
#                                 if payload:
#                                     body += payload.decode("utf-8", errors="replace")
#                             except Exception:
#                                 pass
#                 else:
#                     try:
#                         payload = msg.get_payload(decode=True)
#                         if payload:
#                             body = payload.decode("utf-8", errors="replace")
#                     except Exception:
#                         body = ""

#                 clean_body = clean_text(body)
#                 info = extract_ticket_info(clean_body, subject)

#                 ticket_type, current_task_id, display_parent_id, display_short_desc = determine_task_identity(info)

#                 if current_task_id == "N/A" or current_task_id in processed_tasks:
#                     continue

#                 assigned_team_key = None
#                 if "scg-wifi@inetms.co.th" in to_address:
#                     assigned_team_key = "iNET Network Team"
#                 elif "scgcloud@inetms.co.th" in to_address:
#                     assigned_team_key = "iNET Operation Team"
#                 elif "inetmscloud@inetms.co.th" in to_address:
#                     assigned_team_key = "iNET Cloud Support Team"

#                 if not assigned_team_key:
#                     continue

#                 final_route = "GCP & AWS Team (Both)"
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
#                         short_desc=display_short_desc,
#                         ritm_desc=info.get("ritm_short_desc", ""),
#                         description=info.get("description", ""),
#                         env=info.get("related_env", ""),
#                         body_text=clean_body,
#                     )

#                     if ml_prediction and ml_confidence >= ML_CONFIDENCE_THRESHOLD:
#                         final_route = ml_prediction
#                         prediction_source = "ML"
#                         print(
#                             f"🤖 ML_ROUTER | Task={current_task_id} "
#                             f"| Team={final_route} "
#                             f"| Confidence={ml_confidence:.2%}"
#                         )
#                     else:
#                         final_route = route_by_rules(info, clean_body)
#                         prediction_source = "RULE_FALLBACK"
#                         print(
#                             f"⚠️ RULE_FALLBACK | Task={current_task_id} "
#                             f"| ML={ml_prediction} "
#                             f"| Confidence={ml_confidence:.2%} "
#                             f"| Final={final_route}"
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
#                 }

#                 if display_parent_id not in ritm_groups:
#                     ritm_groups[display_parent_id] = []

#                 ritm_groups[display_parent_id].append(task_obj)
#                 processed_tasks.add(current_task_id)

#             except Exception as e:
#                 # print(f"❌ Error processing message ID {printable_id}: {e}")
#                 print(f"❌ Error processing message ID: {e}")

#         # =================================================
#         # Cross-Task Logic
#         # =================================================
#         for ritm_id, tasks in ritm_groups.items():
#             if len(tasks) > 1:
#                 known_team = None
#                 for t in tasks:
#                     if t["final_route"] in ["GCP Team", "AWS Team"]:
#                         known_team = t["final_route"]
#                         break

#                 if known_team:
#                     for t in tasks:
#                         if t["final_route"] == "GCP & AWS Team (Both)":
#                             t["final_route"] = "AWS Team" if known_team == "GCP Team" else "GCP Team"
#                             if t["prediction_source"] == "RULE_FALLBACK":
#                                 t["prediction_source"] = "CROSS_TASK_INFERENCE"

#             all_tasks_list.extend(tasks)

#         all_tasks_list.sort(key=lambda x: x["sent_date"])

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

# TODO ---------------------------------------------------------- old version model

# import imaplib
# import email
# import joblib  # สำหรับโหลดโมเดล ML
# import os
# from datetime import datetime, timedelta
# from app.config import Config
# from app.utils.parser import clean_text, extract_ticket_info
# from app.utils.ml_utils import thai_tokenizer

# # --- 1. Load ML Model ---
# # ระบุตำแหน่งไฟล์โมเดลที่เทรนไว้
# MODEL_PATH = os.path.join("model", "ticket_classifier_model.pkl")
# try:
#     ml_model = joblib.load(MODEL_PATH)
#     print("✅ ML Model loaded successfully with PyThaiNLP support.")
# except Exception as e:
#     print(f"⚠️ Warning: Could not load ML model: {e}")
#     ml_model = None

# processed_tasks = set()
    
# def predict_team_with_ml(text):
#     """ฟังก์ชันช่วยทำนายทีมด้วย ML พร้อมเช็คค่าความเชื่อมั่น"""
#     if not ml_model:
#         return None, 0.0
#     try:
#         # ตรวจสอบว่า text ไม่ว่างเปล่า
#         if not text.strip():
#             return None, 0.0
            
#         prediction = ml_model.predict([text])[0]
#         probabilities = ml_model.predict_proba([text])
#         confidence = probabilities.max()
#         return prediction, confidence
#     except Exception as e:
#         # พิมพ์ Error ออกมาดูว่าติดอะไร (เช่น หา tokenizer ไม่เจอ)
#         print(f"❌ ML Prediction Error: {e}") 
#         return None, 0.0

# def fetch_and_group_tasks():
#     all_tasks_list = []
#     ritm_groups = {}
#     mail = None

#     try:
#         mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=30) 
#         mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
#         mail.select("scg")

#         since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
#         _, messages = mail.search(None, f'(SINCE "{since_date}")')
#         ids = messages[0].split()

#         if not ids: return []

#         for m_id in reversed(ids):
#             try:
#                 _, msg_data = mail.fetch(m_id, "(RFC822)")
#                 if not msg_data or not msg_data[0]: continue
                
#                 msg = email.message_from_bytes(msg_data[0][1])
#                 date_str = msg.get("Date")
#                 msg_date = email.utils.parsedate_to_datetime(date_str)
#                 subject = msg.get("Subject", "")

#                 if Config.TARGET_SENDER not in msg.get("From", ""): continue

#                 to_address = msg.get("To", "").lower()
#                 body = ""
#                 if msg.is_multipart():
#                     for part in msg.walk():
#                         if part.get_content_type() in ["text/plain", "text/html"]:
#                             try: body += part.get_payload(decode=True).decode('utf-8', errors='replace')
#                             except: pass
#                 else:
#                     body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

#                 clean_body = clean_text(body)
#                 info = extract_ticket_info(clean_body, subject)

#                 current_task_id = "N/A"
#                 display_parent_id = "N/A"
#                 display_short_desc = "N/A"

#                 if info["is_valid_itask"]:
#                     current_task_id = info["itask_no"]
#                     display_parent_id = info["itask_no"]
#                     display_short_desc = info["inc_short_desc"]
#                 elif info["is_valid_ritm"]:
#                     current_task_id = info["task_no"]
#                     display_parent_id = info["ritm_no"]
#                     display_short_desc = info["task_short_desc"]
#                 elif info["is_valid_ctask"]:
#                     current_task_id = info["ctask_no"]
#                     display_parent_id = info["ctask_no"]
#                     display_short_desc = info["ctask_short_desc"]

#                 if current_task_id == "N/A" or current_task_id in processed_tasks:
#                     continue

#                 # --- 2. Advanced Decision Matrix (Hybrid Mode) ---
#                 final_route = "GCP & AWS Team (Both)"
#                 assigned_team_key = None
#                 if "scg-wifi@inetms.co.th" in to_address:
#                     assigned_team_key = "iNET Network Team"
#                 elif "scgcloud@inetms.co.th" in to_address:
#                     assigned_team_key = "iNET Operation Team"
#                 elif "inetmscloud@inetms.co.th" in to_address:
#                     assigned_team_key = "iNET Cloud Support Team"

#                 if assigned_team_key == "iNET Network Team":
#                     final_route = "iNET Network Team"
#                 elif assigned_team_key == "iNET Operation Team":
#                     final_route = "iNET Operation Team"
#                 elif assigned_team_key == "iNET Cloud Support Team":
                    
#                     # --- [จุดแก้ไข: นำ ML มาใช้งาน] ---
#                     # รวมข้อความสำหรับส่งให้ ML วิเคราะห์
#                     text_for_ml = f"{display_short_desc} {info['description']} {info['related_env']}".replace('\n', ' ')
                    
#                     predicted_team, score = predict_team_with_ml(text_for_ml)
                    
#                     # ถ้า ML มั่นใจมากกว่า 75% ให้เชื่อ AI
#                     if predicted_team and score > 0.75:
#                         final_route = predicted_team
#                         print(f"🤖 [ML_MATCH] Task: {current_task_id} | Team: {final_route} | Confidence: {score:.2%}")
#                     else:
#                         reason = "Low Confidence" if predicted_team else "Model Error"
#                         print(f"⚠️ [FALLBACK] Task: {current_task_id} | Reason: {reason} ({score:.2%}) -> Switching to Rule-based")
                        
#                         # Fallback: ถ้า AI ไม่มั่นใจ ให้กลับไปใช้ Rule-based Logic เดิม
#                         full_content = clean_body.upper()
#                         env_text = info["related_env"].upper()
#                         task_header = info["task_short_desc"].upper()
#                         ritm_header = info["ritm_short_desc"].upper()
#                         ritm_desc = info["description"].upper()
#                         found_team = False

#                         # A. เช็คจาก IP
#                         if info["ips"]:
#                             if any("41" in ip for ip in info["ips"]): final_route = "AWS Team"; found_team = True
#                             elif any("42" in ip for ip in info["ips"]): final_route = "GCP Team"; found_team = True

#                         # B. เช็คจาก URL
#                         if not found_team:
#                             for url in info["urls"]:
#                                 for domain, team in Config.SYSTEM_MAPPING.items():
#                                     if domain in url.lower(): final_route = team; found_team = True; break
#                                 if found_team: break

#                         # C. Keyword Hierarchy
#                         if not found_team:
#                             combined_headers = (task_header + " " + ritm_header).upper()
#                             is_header_gcp = any(k in combined_headers for k in ["[GCP]", "GCP", "GOOGLE"])
#                             is_header_aws = any(k in combined_headers for k in ["[AWS]", "AWS", "AMAZON"])

#                             if is_header_gcp and not is_header_aws:
#                                 final_route = "GCP Team"; found_team = True
#                             elif is_header_aws and not is_header_gcp:
#                                 final_route = "AWS Team"; found_team = True

#                         # D. Description Search
#                         if not found_team:
#                             desc_has_gcp = any(k in full_content for k in ["GOOGLE", "GCP", "GEMINI", "GOOGLE WORKSPACE"])
#                             desc_has_aws = any(k in full_content for k in ["AWS", "AMAZON", "AWS HUB"])
#                             if (env_text.count("GCP") > 0 or desc_has_gcp) and not desc_has_aws: final_route = "GCP Team"; found_team = True
#                             elif (env_text.count("AWS") > 0 or desc_has_aws) and not desc_has_gcp: final_route = "AWS Team"; found_team = True

#                         if not found_team:
#                             header_content = ritm_header + " " + ritm_desc
#                             is_header_gcp = any(k in header_content for k in ["[GCP]", "GOOGLE", "GCP"])
#                             is_header_aws = any(k in header_content for k in ["[AWS]", "AMAZON", "AWS"])
#                             if is_header_gcp and not is_header_aws: final_route = "GCP Team"; found_team = True
#                             elif is_header_aws and not is_header_gcp: final_route = "AWS Team"; found_team = True

#                 else:
#                     continue

#                 # เก็บข้อมูลลงกลุ่ม RITM
#                 task_obj = {
#                     "task": current_task_id,
#                     "ritm": display_parent_id,
#                     "short_desc": display_short_desc,
#                     "env": info["related_env"],
#                     "final_route": final_route,
#                     "sent_date": msg_date
#                 }
                
#                 if display_parent_id not in ritm_groups:
#                     ritm_groups[display_parent_id] = []
#                 ritm_groups[display_parent_id].append(task_obj)
#                 processed_tasks.add(current_task_id)

#             except Exception as e:
#                 print(f"❌ Error processing message: {e}")

#         # --- [Cross-Task Logic] ---
#         for ritm_id, tasks in ritm_groups.items():
#             if len(tasks) > 1:
#                 known_team = None
#                 for t in tasks:
#                     if t["final_route"] in ["GCP Team", "AWS Team"]:
#                         known_team = t["final_route"]
#                         break
                
#                 if known_team:
#                     for t in tasks:
#                         if t["final_route"] == "GCP & AWS Team (Both)":
#                             if known_team == "GCP Team":
#                                 t["final_route"] = "AWS Team"
#                             else:
#                                 t["final_route"] = "GCP Team"

#             all_tasks_list.extend(tasks)

#         all_tasks_list.sort(key=lambda x: x["sent_date"])
#         mail.logout()

#     except Exception as e:
#         print(f"📧 IMAP Error: {e}")
#     finally:
#         if mail:
#             try: mail.close()
#             except: pass

#     return all_tasks_list