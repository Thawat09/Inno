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

# TODO ----------------------------------------------------------

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
                    
#                     # ถ้า ML มั่นใจมากกว่า 70% ให้เชื่อ AI
#                     if predicted_team and score > 0.70:
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