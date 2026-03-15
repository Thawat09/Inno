import google.generativeai as genai
from app.config import Config

def predict_with_gemini(text_input):
    if not Config.GOOGLE_API_KEY:
        return None

    try:
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        model = genai.GenerativeModel(Config.LLM_MODEL_NAME)
        
        prompt = f"""
            คุณคือผู้เชี่ยวชาญด้าน IT Support ของทีม iNET Cloud Support 
            หน้าที่ของคุณคือวิเคราะห์ข้อมูล Ticket และตัดสินใจเลือก Sub-team ("AWS Team" หรือ "GCP Team") 

            [ลำดับความสำคัญในการพิจารณา (Hierarchy)]
            1. ตรวจสอบ Prefix: หากใน Subject หรือ Short Description มีตัวอักษร [AWS] ให้เลือก "AWS Team" หรือถ้ามี [GCP] ให้เลือก "GCP Team" ทันที
            2. ตรวจสอบ Hub: หากพบคำว่า "AWS HUB" ให้เลือก "AWS Team" | "GCP HUB" ให้เลือก "GCP Team"
            3. ตรวจสอบ IP Address: 
            - หากพบ IP ที่ขึ้นต้นด้วย 10.41.xx.xx ให้เลือก "AWS Team"
            - หากพบ IP ที่ขึ้นต้นด้วย 10.42.xx.xx ให้เลือก "GCP Team"
            4. ตรวจสอบระบบและพนักงานเฉพาะทาง:
            - หากพบชื่อ "PHASSAKORN SEENIL" หรือบริการ "S3", "EC2", "RDS" ให้เลือก "AWS Team"
            - หากพบคำว่า "GEMINI", "GOOGLE WORKSPACE", "CLOUD RUN", "SPOKE01", "SHAREDSERVICES-PRD-RG" ให้เลือก "GCP Team"

            [เงื่อนไขการตัดสินใจ]
            - ตัดสินใจเลือก "AWS Team" หากข้อมูลเอนเอียงไปทาง Amazon Web Services
            - ตัดสินใจเลือก "GCP Team" หากข้อมูลเอนเอียงไปทาง Google Cloud Platform
            - หากพบทั้งคู่ในสัดส่วนที่เท่ากัน หรือข้อมูลขัดแย้งกันอย่างรุนแรง ให้ตอบ "GCP & AWS Team (Both)"

            [ข้อมูล Ticket สำหรับวิเคราะห์]
            {text_input}

            [ข้อบังคับในการตอบ]
            - ตอบเพียงชื่อทีมเท่านั้น ห้ามมีคำบรรยายอื่นประกอบ: "AWS Team", "GCP Team" หรือ "GCP & AWS Team (Both)"
            """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        return None