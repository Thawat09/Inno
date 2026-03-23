import requests

from app.config import Config


def get_line_headers():
    return {
        "Authorization": f"Bearer {Config.LINE_ACCESS_TOKEN}"
    }


def get_chat_identity(source):
    stype = source.get("type")

    if stype == "group":
        return "group", source.get("groupId")
    elif stype == "room":
        return "room", source.get("roomId")
    elif stype == "user":
        return "user", source.get("userId")

    return None, None


def get_profile_data(source, user_id):
    if not user_id:
        return {
            "display_name": None,
            "picture_url": None,
            "status_message": None,
            "language": None
        }

    stype = source.get("type")

    if stype == "group":
        url = f"https://api.line.me/v2/bot/group/{source.get('groupId')}/member/{user_id}"
    elif stype == "room":
        url = f"https://api.line.me/v2/bot/room/{source.get('roomId')}/member/{user_id}"
    else:
        url = f"https://api.line.me/v2/bot/profile/{user_id}"

    try:
        res = requests.get(url, headers=get_line_headers(), timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "display_name": data.get("displayName"),
                "picture_url": data.get("pictureUrl"),
                "status_message": data.get("statusMessage"),
                "language": data.get("language")
            }
    except Exception as e:
        print(f"❌ get_profile_data error: {str(e)}")

    return {
        "display_name": None,
        "picture_url": None,
        "status_message": None,
        "language": None
    }


def get_group_summary(group_id):
    if not group_id:
        return {}

    url = f"https://api.line.me/v2/bot/group/{group_id}/summary"

    try:
        res = requests.get(url, headers=get_line_headers(), timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"❌ get_group_summary error: {str(e)}")

    return {}