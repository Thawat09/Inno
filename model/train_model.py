import sys
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from pythainlp.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.ml_utils import thai_tokenizer

# 1. โหลดข้อมูลที่เตรียมไว้
df = pd.read_csv('ticket_training_data.csv')

# ล้างข้อมูลเบื้องต้น (ลบแถวที่ไม่มีข้อความ)
df['combined_features'] = (
    "SUBJECT: " + df['subject'].fillna('') + " | " +
    "TASK_DESC: " + df['task_short_desc'].fillna('') + " | " +
    "RITM_DESC: " + df['ritm_short_desc'].fillna('') + " | " +
    "DETAIL: " + df['description'].fillna('') + " | " +
    "ENV: " + df['related_env'].fillna('')
)

X = df['combined_features']  # ข้อความที่จะใช้เรียนรู้
y = df['target_team']   # ทีมที่เป็นคำตอบ

# 2. แบ่งข้อมูลเป็นชุดสอน (Train) 80% และชุดทดสอบ (Test) 20%
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. สร้าง Pipeline สำหรับประมวลผล
# TF-IDF: เปลี่ยนข้อความเป็นตัวเลขที่มีน้ำหนักตามความสำคัญของคำ
# Logistic Regression: อัลกอริทึมสำหรับแยกประเภททีม
model = Pipeline([
    ('tfidf', TfidfVectorizer(
        tokenizer=thai_tokenizer, # ใช้ฟังก์ชันตัดคำไทยที่เราสร้าง
        ngram_range=(1, 2), 
        min_df=2,           # ตัดคำที่ปรากฏเพียงครั้งเดียวทิ้งเพื่อลด Noise
        max_df=0.9,         # ตัดคำที่ปรากฏบ่อยเกินไป (เช่น "Catalog") ทิ้ง
        use_idf=True,
        token_pattern=None  # ต้องตั้งเป็น None เมื่อใช้ custom tokenizer
    )),
    ('clf', LogisticRegression(
        class_weight='balanced', # ให้ความสำคัญกับทีมที่มีข้อมูลน้อย (เช่น Both) มากขึ้น
        max_iter=1000
    ))
])

# 4. เริ่มการสอน (Training)
print("⏳ ระบบกำลังเรียนรู้จากข้อมูลที่คุณเตรียมไว้...")
model.fit(X_train, y_train)

# 5. ทดสอบความแม่นยำ (Evaluation)
y_pred = model.predict(X_test)
print("\n📊 ผลการทดสอบความแม่นยำ (Model Report):")
print(f"Overall Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print(classification_report(y_test, y_pred, zero_division=0))

# 6. บันทึกโมเดลไว้ใช้งานจริง
joblib.dump(model, 'ticket_classifier_model.pkl')
print("\n✅ บันทึกโมเดลเรียบร้อยในชื่อ: 'ticket_classifier_model.pkl'")