from flask import Blueprint, request, jsonify
import hmac, hashlib, base64
import requests
from app.config import Config

webhook_bp = Blueprint('webhook', __name__)

def verify_signature(body, signature):
    hash = hmac.new(Config.LINE_CHANNEL_SECRET.encode('utf-8'), body, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(hash).decode('utf-8'), signature)

def get_display_name(source, user_id):
    headers = {"Authorization": f"Bearer {Config.LINE_ACCESS_TOKEN}"}
    stype = source.get("type")
    if stype == "group":
        url = f"https://api.line.me/v2/bot/group/{source.get('groupId')}/member/{user_id}"
    elif stype == "room":
        url = f"https://api.line.me/v2/bot/room/{source.get('roomId')}/member/{user_id}"
    else:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"
    
    res = requests.get(url, headers=headers, timeout=10)
    return res.json().get("displayName", "Unknown") if res.status_code == 200 else "Unknown"

@webhook_bp.route("/webhook", methods=["POST"])
def line_webhook():
    body = request.get_data()
    signature = request.headers.get("X-Line-Signature", "")
    
    if not verify_signature(body, signature):
        return "Unauthorized", 400

    data = request.get_json()
    for event in data.get("events", []):
        source = event.get("source", {})
        uid = source.get("userId")
        
        # ส่วนที่ 1: ตรวจจับคนเข้ากลุ่ม
        if event["type"] == "memberJoined":
            for m in event.get("joined", {}).get("members", []):
                name = get_display_name(source, m.get("userId"))
                print(f"🆕 New Member: {name} (ID: {m.get('userId')})")

        # ส่วนที่ 2: ตรวจจับการกดปุ่ม "รับทราบ"
        elif event["type"] == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"]
            if text.startswith("รับทราบ"):
                name = get_display_name(source, uid)
                print("\n" + "="*45)
                print(f"👷 งานถูกรับแล้วโดย: {name}")
                print(f"💬 ข้อความ: {text}")
                print("="*45 + "\n")
                
        # ส่วนที่ 3: ตรวจจับคนออกจากกลุ่ม (Member Left)
        elif event["type"] == "memberLeft":
            for m in event.get("left", {}).get("members", []):
                uid_left = m.get("userId")
                # หมายเหตุ: ตรงนี้ get_display_name จะใช้ไม่ได้แล้วเพราะเขาไม่อยู่ในกลุ่ม
                print(f"❌ Member Left: User ID {uid_left}")

        # ส่วนที่ 4: ตรวจจับเมื่อ "ตัวบอทเอง" ถูกเตะออกจากกลุ่ม
        elif event["type"] == "leave":
            group_id = source.get("groupId") or source.get("roomId")
            print(f"🏠 Bot has been removed from Group/Room: {group_id}")

        # ส่วนที่ 5: ตรวจจับเมื่อ "ตัวบอทเอง" ถูกเชิญเข้ากลุ่ม
        elif event["type"] == "join":
            print(f"🤝 Bot joined a new group: {source.get('groupId')}")

    return jsonify({"status": "ok"})