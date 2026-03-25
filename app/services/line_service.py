from app.config import Config
from app.services.line_api import push_message
from app.services.line_payloads import (
    build_task_notification_payload,
    build_daily_summary_payload
)
from app.services.team_repository import get_staffs_by_team


def send_task_notification(analysis: dict):
    team_name = analysis.get("final_route", "Unknown")
    staffs = get_staffs_by_team(team_name)

    payload = build_task_notification_payload(
        analysis=analysis,
        team_name=team_name,
        staffs=staffs,
        group_id=Config.LINE_GROUP_ID
    )

    r = push_message(payload)

    if r.status_code != 200:
        print(f"❌ LINE API Error: {r.status_code} - {r.text}")
    else:
        if staffs:
            print(f"✅ LINE Sent Successfully to {team_name} -> {[s['name'] for s in staffs]}")
        else:
            print(f"⚠️ No active staff found for team: {team_name}")

    return r.status_code


def send_daily_summary_notification(summary: dict):
    payload = build_daily_summary_payload(
        summary=summary,
        group_id=Config.LINE_GROUP_ID
    )

    r = push_message(payload)

    if r.status_code != 200:
        print(f"❌ LINE Daily Summary API Error: {r.status_code} - {r.text}")
    else:
        print(f"✅ LINE Daily Summary Sent Successfully: {summary['report_date_th']}")

    return r.status_code