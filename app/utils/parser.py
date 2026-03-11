import re
from bs4 import BeautifulSoup

def clean_text(text):
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator='\n')

def extract_ticket_info(body, subject=""):
    # ปรับ Pattern ของ state ให้เจาะจงว่าต้องอยู่หลัง Catalog Task Details เท่านั้น
    patterns = {
        # --- Service Request (RITM/TASK) ---
        "ritm_no": r"Service Request Number:\s*(RITM\d+)",
        "task_no": r"Task Number:\s*(TASK\d+)",
        "ritm_short_desc": r"Service Request Details:.*?Short Description:\s*(.*?)(?:\n|Description:|$)",
        "task_short_desc": r"Catalog Task Details:.*?Short Description:\s*(.*?)(?:\n|Click here to view the task|$)",
        
        # --- Incident (INC/ITASK) ---
        "inc_no": r"Number:\s*(INC\d+)",
        "itask_no": r"Number:\s*(ITASK\d+)",
        "inc_short_desc": r"Short Description:\s*(.*?)(?:\n|Description:|$)",

        # --- Change Task (CTASK) ---
        "ctask_no": r"Number:\s*(CTASK\d+)",
        "ctask_short_desc": r"Number:\s*CTASK\d+.*?Short Description:\s*(.*?)(?:\n|Description:|$)",
        
        # --- Common Info ---
        # แก้ไขจุดนี้: ใช้ lookahead/lookbehind หรือระบุขอบเขตให้ชัดเจน
        "state": r"Catalog Task Details:.*?State:\s*([a-zA-Z\s]+)", 
        "related_env": r"Related environment:(.*?)(?:\n\n|\nไฟล์|$)",
        "description": r"Description:\s*(.*?)(?:\n|Related environment:|$)"
    }
    
    results = {}
    for key, pattern in patterns.items():
        # ใช้ re.DOTALL เพื่อให้ .*? คลุมทุกบรรทัดจนถึงคำว่า State
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
        results[key] = match.group(1).strip() if match else "N/A"
    
    # 1. ดึง URL และ IP Address
    results["urls"] = re.findall(r"https?://[^\s'\"<>]+", body)
    results["ips"] = re.findall(r"10\.(41|42)\.\d{1,3}\.\d{1,3}", body)

    # 2. Filter Logic
    is_ritm_assign = "Catalog Task Assignment" in subject or "A Catalog Task record has been assigned" in body
    is_itask_assign = "Incident Task Assignment" in subject or "A Incident Task record has been assigned" in body
    is_ctask_assign = "Change task" in subject or "A Change Task record has been assigned" in body
    
    # --- [จุดแก้ไขสำคัญ] ---
    # ตรวจสอบสถานะ: เราเอาเฉพาะที่เป็น Assigned หรือถ้าคุณอยากให้ Awaiting ผ่านด้วยก็เพิ่มได้ครับ
    # แต่จากรูป TASK1625065 สถานะข้างล่างคือ 'Assigned' ดังนั้นเช็คแค่นี้ก็ควรผ่านแล้ว
    current_state = results["state"].lower()
    is_assigned_state = "assigned" in current_state or results["state"] == "N/A"
    
    results["is_valid_ritm"] = is_ritm_assign and is_assigned_state
    results["is_valid_itask"] = is_itask_assign
    results["is_valid_ctask"] = is_ctask_assign
    
    return results