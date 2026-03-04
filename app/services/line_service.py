import requests
from app.config import Config

STAFF_MAPPING = {
    "AWS Team": [{"name": "Thawat", "userId": "U2bc72dfa6c8f312da0bf1088f1ad1a44"}],
    "GCP Team": [{"name": "เอิงเอย 🖤", "userId": "Ua8f5ff7cf153d4786d5f2ec03a4db9de"}],
    "GCP & AWS Team (Both)": [
        {"name": "เอิงเอย 🖤", "userId": "Ua8f5ff7cf153d4786d5f2ec03a4db9de"},
        {"name": "Thawat", "userId": "U2bc72dfa6c8f312da0bf1088f1ad1a44"}
    ],
    "iNET Network Team": [
        {"name": "Thawat", "userId": "U2bc72dfa6c8f312da0bf1088f1ad1a44"}
    ],
    "iNET Operation Team": [
        {"name": "Thawat", "userId": "Ua8f5ff7cf153d4786d5f2ec03a4db9de"}
    ],
}

def send_task_notification(analysis: dict):
    push_url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Config.LINE_ACCESS_TOKEN}",
    }

    # Build Mentions
    team_name = analysis.get("final_route", "Unknown")
    staffs = STAFF_MAPPING.get(team_name, [])
    substitution = {}
    mentions = []
    for i, s in enumerate(staffs, start=1):
        key = f"u{i}"
        mentions.append(f"{{{key}}}")
        substitution[key] = {"type": "mention", "mentionee": {"type": "user", "userId": s["userId"]}}
        mention_line = ' '.join(mentions)
        # display_text = f"🚨 New Ticket Assigned {analysis.get('ritm')}!\n\n{mention_line}"
        display_text = f"🚨 New Ticket Assigned {analysis.get('ritm')}!\n🎯 Route: {team_name}\n\n{mention_line}"

    payload = {
        "to": Config.LINE_GROUP_ID,
        "messages": [
            {
                "type": "textV2",
                "text": display_text,
                "substitution": substitution
            },
            {
                "type": "flex",
                "altText": f"New Task: {analysis['task']}",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box", "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "New Ticket Assigned!", "weight": "bold", "color": "#E74C3C", "size": "md"},
                            {"type": "text", "text": f"🔗 RITM: {analysis['ritm']}", "weight": "bold", "size": "sm", "margin": "lg"},
                            {"type": "text", "text": f"📌 Task: {analysis['task']}", "size": "sm", "margin": "xs"},
                            {"type": "text", "text": f"🚀 Route: {team_name}", "weight": "bold", "color": "#2980B9", "size": "sm", "margin": "md"}
                        ]
                    },
                    "footer": {
                        "type": "box", "layout": "vertical",
                        "contents": [{
                            "type": "button", "style": "primary", "color": "#27AE60",
                            "action": {"type": "message", "label": "✅ รับทราบเคสนี้", "text": f"รับทราบ | {analysis['task']} | {analysis['ritm']}"}
                        }]
                    }
                }
            }
        ]
    }
    r = requests.post(push_url, headers=headers, json=payload, timeout=15)

    if r.status_code != 200:
        print(f"❌ LINE API Error: {r.status_code} - {r.text}")
    else:
        print(f"✅ LINE Sent Successfully to {team_name}")

    return r.status_code