import json
import requests
from app.config import Config


VALID_SUB_TEAMS = ["AWS Team", "GCP Team", "GCP & AWS Team (Both)"]


def normalize_llm_output(raw_text):
    if not raw_text:
        return None

    cleaned = raw_text.strip()

    for team in VALID_SUB_TEAMS:
        if cleaned == team:
            return team

    for team in VALID_SUB_TEAMS:
        if team in cleaned:
            return team

    return None


def format_rag_contexts(retrieved_contexts):
    if not retrieved_contexts:
        return "ไม่พบข้อมูลอ้างอิงจาก ticket เก่า"

    lines = []
    for i, item in enumerate(retrieved_contexts, start=1):
        lines.append(
            f"""[Context #{i}]
record_id: {item.get("record_id", "")}
parent_id: {item.get("parent_id", "")}
label_sub_team: {item.get("label_sub_team", "")}
label_source: {item.get("label_source", "")}
decision_mode: {item.get("decision_mode", "")}
email_date: {item.get("email_date", "")}
related_env_raw: {item.get("related_env_raw", "")}
subject_clean: {item.get("subject_clean", "")}
short_desc_clean: {item.get("short_desc_clean", "")}
description_clean: {item.get("description_clean", "")}
retrieval_score: {item.get("retrieval_score", 0)}
"""
        )
    return "\n".join(lines)


def build_cloud_subteam_rag_prompt(text_input, retrieved_contexts):
    context_text = format_rag_contexts(retrieved_contexts)

    return f"""
        คุณคือผู้เชี่ยวชาญด้าน IT Support Routing ของทีม iNET Cloud Support
        หน้าที่ของคุณคือวิเคราะห์ Ticket และเลือก Cloud Sub-team ที่ถูกต้องที่สุด

        [ทีมที่เลือกได้]
        - AWS Team
        - GCP Team
        - GCP & AWS Team (Both)

        [หลักการตัดสิน]
        1. ให้พิจารณา "Ticket ปัจจุบัน" เป็นหลัก
        2. ให้ใช้ "ข้อมูลอ้างอิงจาก Ticket เก่า" เป็นข้อมูลสนับสนุนเท่านั้น
        3. หากกฎจาก Ticket ปัจจุบันชัดเจน ให้ยึด Ticket ปัจจุบันก่อนข้อมูลอ้างอิง
        4. หากข้อมูลอ้างอิงส่วนใหญ่ชี้ไปทีมเดียวกัน และไม่ขัดกับ Ticket ปัจจุบัน ให้ใช้ประกอบการตัดสินได้
        5. หากข้อมูลขัดแย้งกัน หรือ AWS/GCP ปนกันพอ ๆ กัน ให้ตอบ "GCP & AWS Team (Both)"

        [ลำดับความสำคัญในการพิจารณา]
        1. Prefix
        - หากใน Subject หรือ Short Description มี [AWS] และไม่มี [GCP] ให้เลือก "AWS Team" ทันที
        - หากใน Subject หรือ Short Description มี [GCP] และไม่มี [AWS] ให้เลือก "GCP Team" ทันที

        2. Hub
        - หากพบ "AWS HUB" ให้เลือก "AWS Team"
        - หากพบ "GCP HUB" ให้เลือก "GCP Team"
        - หากพบ "FIREWALL REQUEST : AWS HUB" ให้เลือก "AWS Team"
        - หากพบ "FIREWALL REQUEST : GCP HUB" ให้เลือก "GCP Team"

        3. IP Address
        - หากพบ IP ที่ขึ้นต้นด้วย 10.41. ให้เลือก "AWS Team"
        - หากพบ IP ที่ขึ้นต้นด้วย 10.42. ให้เลือก "GCP Team"

        4. AWS indicators
        - หากพบตัวบ่งชี้ต่อไปนี้ใน Subject, Short Description, Related Environment, Description หรือ Body
        [AWS], AWS, AMAZON, AWS HUB, EC2, ALB, NLB, ELB, ACM, ROUTE 53, WAF, S3, RDS, LAMBDA, CLOUDFRONT, EKS, ECS, BEDROCK, IAM, PHASSAKORN SEENIL
        และไม่มีสัญญาณของ GCP ที่ขัดแย้งอย่างมีนัยสำคัญ ให้เอนเอียงไปทาง "AWS Team"

        5. GCP indicators
        - หากพบตัวบ่งชี้ต่อไปนี้ใน Subject, Short Description, Related Environment, Description หรือ Body
        [GCP], GCP, GCP PROJECT, GOOGLE, GOOGLE WORKSPACE, GOOGLE CLOUD, GKE, GCS, BIGQUERY, CLOUDRUN, APPENGINE, GCP USER, GOOGLE SHEET, WORKSPACE, GEMINI, CLOUDFUNCTIONS, CLOUD RUN, SPOKE01, SHAREDSERVICES-PRD-RG
        และไม่มีสัญญาณของ AWS ที่ขัดแย้งอย่างมีนัยสำคัญ ให้เอนเอียงไปทาง "GCP Team"

        6. Related Environment / Description / Body
        - หากข้อมูลใน Related Environment, Description หรือ Body เอนเอียงไปทาง AWS อย่างชัดเจน ให้ตอบ "AWS Team"
        - หากข้อมูลใน Related Environment, Description หรือ Body เอนเอียงไปทาง GCP อย่างชัดเจน ให้ตอบ "GCP Team"
        - คำว่า "เอนเอียงอย่างชัดเจน" หมายถึงมีชื่อ service, project, environment, account, network, IP, keyword หรือข้อความอธิบายที่สัมพันธ์กับฝั่งใดฝั่งหนึ่งชัดเจนมากกว่าอีกฝั่ง
        - หากพบทั้ง AWS และ GCP ในระดับใกล้เคียงกัน หรือข้อความเกี่ยวข้องกับการเชื่อมต่อข้าม cloud ให้ตอบ "GCP & AWS Team (Both)"

        [การใช้ข้อมูลอ้างอิงจาก Ticket เก่า]
        - ให้ใช้ข้อมูลอ้างอิงเพื่อช่วยดู pattern ว่า Ticket ลักษณะคล้ายกันในอดีตมักถูก route ไปทีมใด
        - หากข้อมูลอ้างอิงส่วนใหญ่ชี้ไป AWS Team และไม่ขัดกับ Ticket ปัจจุบัน ให้เอนเอียงไปทาง "AWS Team"
        - หากข้อมูลอ้างอิงส่วนใหญ่ชี้ไป GCP Team และไม่ขัดกับ Ticket ปัจจุบัน ให้เอนเอียงไปทาง "GCP Team"
        - หากข้อมูลอ้างอิงมีทั้ง AWS และ GCP ปะปนกัน หรือขัดกับ Ticket ปัจจุบัน ห้ามสรุปจากข้อมูลอ้างอิงเพียงอย่างเดียว
        - ห้ามใช้ข้อมูลอ้างอิง override กฎ Prefix, Hub และ IP Address ของ Ticket ปัจจุบัน

        [กฎสำคัญ]
        - หากพบทั้ง AWS และ GCP พอ ๆ กัน หรือข้อมูลขัดแย้งกัน ให้ตอบ "GCP & AWS Team (Both)"
        - หากข้อมูลไม่พอ ให้ตอบ "GCP & AWS Team (Both)"
        - ให้ตอบเฉพาะชื่อทีมเท่านั้น ห้ามมีคำอธิบาย
        - ห้ามตอบอย่างอื่นนอกเหนือจาก:
        AWS Team
        GCP Team
        GCP & AWS Team (Both)

        [ข้อมูล Ticket ปัจจุบัน]
        {text_input}

        [ข้อมูลอ้างอิงจาก Ticket เก่า]
        {context_text}
        """.strip()


def call_ollama(prompt: str):
    ollama_url = getattr(Config.OLLAMA_URL)
    ollama_model = getattr(Config.OLLAMA_MODEL_NAME)
    ollama_timeout = int(getattr(Config.OLLAMA_TIMEOUT))

    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0
        }
    }

    response = requests.post(
        ollama_url,
        json=payload,
        timeout=ollama_timeout
    )
    response.raise_for_status()

    data = response.json()
    return (data.get("response") or "").strip()


def predict_with_ollama_rag(text_input, retrieved_contexts):
    try:
        prompt = build_cloud_subteam_rag_prompt(text_input, retrieved_contexts)
        raw_result = call_ollama(prompt)
        normalized_result = normalize_llm_output(raw_result)

        print(f"🤖 Ollama raw result: {raw_result}")
        print(f"🤖 Ollama normalized result: {normalized_result}")

        return normalized_result

    except Exception as e:
        print(f"⚠️ Ollama API Error: {e}")
        return None