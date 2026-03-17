from google import genai
from app.config import Config


VALID_SUB_TEAMS = ["AWS Team", "GCP Team", "GCP & AWS Team (Both)"]


def build_cloud_subteam_prompt(text_input):
    return f"""
คุณคือผู้เชี่ยวชาญด้าน IT Support Routing ของทีม iNET Cloud Support
หน้าที่ของคุณคือวิเคราะห์ Ticket และเลือก Cloud Sub-team ที่ถูกต้องที่สุด

[ทีมที่เลือกได้]
- AWS Team
- GCP Team
- GCP & AWS Team (Both)

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
- [AWS], AWS, AMAZON, AWS HUB, EC2, ALB, NLB, ELB, ACM, ROUTE 53, WAF, S3, RDS, LAMBDA, CLOUDFRONT, EKS, ECS, BEDROCK, IAM, PHASSAKORN SEENIL

5. GCP indicators
- [GCP], GCP, GCP PROJECT, GOOGLE, GOOGLE WORKSPACE, GOOGLE CLOUD, GKE, GCS, BIGQUERY, CLOUDRUN, APPENGINE, GCP USER, GOOGLE SHEET, WORKSPACE, GEMINI, CLOUDFUNCTIONS, CLOUD RUN, SPOKE01, SHAREDSERVICES-PRD-RG

6. Related Environment / Description / Body
- ถ้าข้อมูลเอนเอียงไปทาง AWS ชัดเจน ให้ตอบ "AWS Team"
- ถ้าข้อมูลเอนเอียงไปทาง GCP ชัดเจน ให้ตอบ "GCP Team"

[กฎสำคัญ]
- หากพบทั้ง AWS และ GCP พอ ๆ กัน หรือข้อมูลขัดแย้งกัน ให้ตอบ "GCP & AWS Team (Both)"
- หากข้อมูลไม่พอ ให้ตอบ "GCP & AWS Team (Both)"
- ให้ตอบเฉพาะชื่อทีมเท่านั้น ห้ามมีคำอธิบาย

[ข้อมูล Ticket]
{text_input}
""".strip()


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


def predict_with_gemini(text_input):
    if not Config.GOOGLE_API_KEY:
        return None

    try:
        client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        prompt = build_cloud_subteam_prompt(text_input)

        response = client.models.generate_content(
            model=Config.LLM_MODEL_NAME,
            contents=prompt,
        )

        raw_result = response.text.strip() if response and response.text else None
        normalized_result = normalize_llm_output(raw_result)

        print(f"🤖 Gemini raw result: {raw_result}")
        print(f"🤖 Gemini normalized result: {normalized_result}")

        return normalized_result

    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        return None