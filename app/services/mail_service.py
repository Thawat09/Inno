import imaplib, email
from datetime import datetime, timedelta
from app.config import Config
from app.utils.parser import clean_text, extract_ticket_info

processed_tasks = set()

def fetch_and_group_tasks():
    all_tasks_list = []
    mail = None 
    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, timeout=30) 
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        mail.select("scg")

        since_date = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(SINCE "{since_date}")')
        ids = messages[0].split()
        if not ids: return {}

        for m_id in reversed(ids):
            try:
                _, msg_data = mail.fetch(m_id, "(RFC822)")
                if not msg_data or not msg_data[0]: continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                # ดึงวันที่จาก Header ของเมลเพื่อใช้ตรวจสอบความถูกต้องในการเรียง
                date_str = msg.get("Date")
                msg_date = email.utils.parsedate_to_datetime(date_str)
                subject = msg.get("Subject", "")
                if Config.TARGET_SENDER not in msg.get("From", ""): continue

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

                # --- 1. คัดกรองประเภทเมลและเลือก ID (Filter & ID Selection) ---
                current_task_id = "N/A"
                display_parent_id = "N/A"
                display_short_desc = "N/A"

                if info["is_valid_itask"]:
                    current_task_id = info["itask_no"]
                    display_parent_id = info["itask_no"] # INC ให้ส่งแค่เลข ITASK
                    display_short_desc = info["inc_short_desc"]
                elif info["is_valid_ritm"]:
                    current_task_id = info["task_no"]
                    display_parent_id = info["ritm_no"]
                    display_short_desc = info["ritm_short_desc"]

                # ถ้าไม่ใช่ Assignment Mail หรือเคยส่งแล้ว ให้ข้าม
                if current_task_id == "N/A":
                    continue
                    
                if current_task_id in processed_tasks:
                    continue

                # --- 2. Advanced Decision Matrix (รวม Logic เก่าแบบละเอียด + ของใหม่) ---
                full_content = clean_body.upper()
                env_text = info["related_env"].upper()
                task_header = info["task_short_desc"].upper()
                final_route = "GCP & AWS Team (Both)"
                found_team = False

                # A. เช็คจาก IP Address (ความแม่นยำอันดับ 1)
                if info["ips"]:
                    if any("41" in ip for ip in info["ips"]): final_route = "AWS Team"; found_team = True
                    elif any("42" in ip for ip in info["ips"]): final_route = "GCP Team"; found_team = True

                # B. เช็คจาก URL ระบบ (ความแม่นยำอันดับ 2 - เช่น justperform)
                if not found_team:
                    for url in info["urls"]:
                        for domain, team in Config.SYSTEM_MAPPING.items():
                            if domain in url.lower(): final_route = team; found_team = True; break
                        if found_team: break

                # C. Logic เก่าแบบละเอียด (Keyword Hierarchy)
                if not found_team:
                    # เช็คคำสำคัญในเนื้อหาและหัวข้อ
                    env_has_gcp = "GCP" in env_text
                    env_has_aws = "AWS" in env_text
                    desc_has_gcp = any(k in full_content for k in ["GOOGLE CLOUD", "GCP", "GEMINI"])
                    desc_has_aws = any(k in full_content for k in ["AWS", "AMAZON", "AWS HUB"])
                    
                    # เช็คจาก Task Header โดยตรง
                    task_specific_team = None
                    if "GCP" in task_header: task_specific_team = "GCP Team"
                    elif "AWS" in task_header: task_specific_team = "AWS Team"

                    # เริ่มการตัดสินใจ Matrix
                    if task_specific_team:
                        final_route = task_specific_team
                    elif env_has_gcp and not env_has_aws:
                        final_route = "GCP Team"
                    elif env_has_aws and not env_has_gcp:
                        final_route = "AWS Team"
                    elif desc_has_gcp and not desc_has_aws:
                        final_route = "GCP Team"
                    elif desc_has_aws and not desc_has_gcp:
                        final_route = "AWS Team"

                # --- 3. บันทึกข้อมูลและจัดกลุ่ม ---
                all_tasks_list.append({
                    "task": current_task_id,
                    "ritm": display_parent_id,
                    "short_desc": display_short_desc,
                    "env": info["related_env"],
                    "final_route": final_route,
                    "sent_date": msg_date
                })

                processed_tasks.add(current_task_id)

            except Exception as e:
                print(f"❌ Error: {e}")

        # เรียงลำดับจากน้อยไปมาก (เก่าไปใหม่)
        all_tasks_list.sort(key=lambda x: x["sent_date"])
        
        mail.logout()
    except Exception as e:
        print(f"📧 IMAP Error: {e}")
    finally:
        if mail:
            try: mail.close()
            except: pass
    return all_tasks_list