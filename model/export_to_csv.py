import imaplib
import email
import re
import csv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# --- 1. CONFIGURATION ---
class Config:
    IMAP_SERVER = "onemail.one.th"
    EMAIL_USER = "thawat.me@inetms.co.th"
    EMAIL_PASS = "TQEAMMFMYJAPNAZN"
    
    TARGET_SENDER = "SCGTicketSystems@service-now.com"
    CSV_FILENAME = "ticket_training_data.csv"
    DAYS_BACK = 30

    SYSTEM_MAPPING = {
        "justperformqas.scg.com": "AWS Team",
        "api-justperformqas.scg.com": "AWS Team",
        "tscpcl.outsystemsenterprise.com": "AWS Team",
        "aws": "AWS Team",
        "gcp": "GCP Team",
        "google": "GCP Team"
    }

# --- 2. UTILS & PARSER ---
def clean_text(text):
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator='\n')

def extract_ticket_info(body, subject=""):
    patterns = {
        "ritm_no": r"Service Request Number:\s*(RITM\d+)",
        "task_no": r"Task Number:\s*(TASK\d+)",
        "ritm_short_desc": r"Service Request Details:.*?Short Description:\s*(.*?)(?:\n|Description:|$)",
        "task_short_desc": r"Catalog Task Details:.*?Short Description:\s*(.*?)(?:\n|Click here to view the task|$)",
        "inc_no": r"Number:\s*(INC\d+)",
        "itask_no": r"Number:\s*(ITASK\d+)",
        "inc_short_desc": r"Short Description:\s*(.*?)(?:\n|Description:|$)",
        "ctask_no": r"Number:\s*(CTASK\d+)",
        "ctask_short_desc": r"Number:\s*CTASK\d+.*?Short Description:\s*(.*?)(?:\n|Description:|$)",
        "state": r"Catalog Task Details:.*?State:\s*([a-zA-Z\s]+)", 
        "related_env": r"Related environment:(.*?)(?:\n\n|\nไฟล์|$)",
        "description": r"Description:\s*(.*?)(?:\n|Related environment:|$)"
    }
    
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
        results[key] = match.group(1).strip() if match else "N/A"
    
    results["urls"] = re.findall(r"https?://[^\s'\"<>]+", body)
    results["ips"] = re.findall(r"10\.(41|42)\.\d{1,3}\.\d{1,3}", body)

    is_ritm_assign = "Catalog Task Assignment" in subject or "A Catalog Task record has been assigned" in body
    is_itask_assign = "Incident Task Assignment" in subject or "A Incident Task record has been assigned" in body
    is_ctask_assign = "Change task" in subject or "A Change Task record has been assigned" in body
    
    current_state = results["state"].lower()
    is_assigned_state = "assigned" in current_state or results["state"] == "N/A"
    
    results["is_valid_ritm"] = is_ritm_assign and is_assigned_state
    results["is_valid_itask"] = is_itask_assign
    results["is_valid_ctask"] = is_ctask_assign
    
    return results

# --- 3. MAIN CORE ---
def run_export():
    processed_tasks = set()
    ritm_groups = {}
    all_extracted_data = []

    print(f"🚀 Starting Email Extraction (Last {Config.DAYS_BACK} days)...")

    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER)
        mail.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        mail.select("scg")

        since_date = (datetime.now() - timedelta(days=Config.DAYS_BACK)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(SINCE "{since_date}")')
        ids = messages[0].split()

        if not ids:
            print("ℹ️ ไม่พบเมลตามเงื่อนไข")
            return

        for m_id in reversed(ids):
            try:
                _, msg_data = mail.fetch(m_id, "(RFC822)")
                if not msg_data or not msg_data[0]: continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "")
                to_address = str(msg.get("To", "")).lower()

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

                # Identify Task & Parent ID
                current_task_id = "N/A"
                display_parent_id = "N/A"
                display_short_desc = "N/A"

                if info["is_valid_itask"]:
                    current_task_id = info["itask_no"]; display_parent_id = info["itask_no"]; display_short_desc = info["inc_short_desc"]
                elif info["is_valid_ritm"]:
                    current_task_id = info["task_no"]; display_parent_id = info["ritm_no"]; display_short_desc = info["task_short_desc"]
                elif info["is_valid_ctask"]:
                    current_task_id = info["ctask_no"]; display_parent_id = info["ctask_no"]; display_short_desc = info["ctask_short_desc"]

                if current_task_id == "N/A" or current_task_id in processed_tasks: continue

                # --- Decision Logic (Exact Copy from Code 1) ---
                final_route = "GCP & AWS Team (Both)"
                assigned_team_key = None
                if "scg-wifi@inetms.co.th" in to_address: assigned_team_key = "iNET Network Team"
                elif "scgcloud@inetms.co.th" in to_address: assigned_team_key = "iNET Operation Team"
                elif "inetmscloud@inetms.co.th" in to_address: assigned_team_key = "iNET Cloud Support Team"

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

                        if is_header_gcp and not is_header_aws: final_route = "GCP Team"; found_team = True
                        elif is_header_aws and not is_header_gcp: final_route = "AWS Team"; found_team = True

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

                # Store object
                task_obj = {
                    "subject": subject.replace('\n', ' ').strip(),
                    "task_short_desc": info["task_short_desc"].replace('\n', ' ').strip(),
                    "ritm_short_desc": info["ritm_short_desc"].replace('\n', ' ').strip(),
                    "description": info["description"].replace('\n', ' ').strip(),
                    "related_env": info["related_env"].replace('\n', ' ').strip(),
                    "target_team": final_route,
                    "task_id": current_task_id,
                    "parent_id": display_parent_id
                }
                
                if display_parent_id not in ritm_groups: ritm_groups[display_parent_id] = []
                ritm_groups[display_parent_id].append(task_obj)
                processed_tasks.add(current_task_id)

            except Exception as e:
                print(f"⚠️ Error message ID {m_id}: {e}")

        # Cross-Task Logic
        for ritm_id, tasks in ritm_groups.items():
            if len(tasks) > 1:
                known_team = next((t["target_team"] for t in tasks if t["target_team"] in ["GCP Team", "AWS Team"]), None)
                if known_team:
                    for t in tasks:
                        if t["target_team"] == "GCP & AWS Team (Both)":
                            t["target_team"] = "AWS Team" if known_team == "GCP Team" else "GCP Team"
            all_extracted_data.extend(tasks)

        # Write CSV
        if all_extracted_data:
            keys = ["subject", "task_short_desc", "ritm_short_desc", "description", "related_env", "target_team", "task_id", "parent_id"]
            with open(Config.CSV_FILENAME, 'w', encoding='utf-8-sig', newline='') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(all_extracted_data)
            print(f"✅ Exported {len(all_extracted_data)} rows to {Config.CSV_FILENAME}")

        mail.logout()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_export()