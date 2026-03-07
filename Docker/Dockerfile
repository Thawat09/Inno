FROM python:3.10-slim

WORKDIR /app

# ติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมดเข้า Container
COPY . .

# สั่งรันโปรแกรมหลัก (สมมติว่าชื่อ main.py)
CMD ["python", "main.py"]