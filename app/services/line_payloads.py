def build_task_notification_payload(analysis: dict, team_name: str, staffs: list, group_id: str):
    substitution = {}
    mentions = []

    for i, s in enumerate(staffs, start=1):
        key = f"u{i}"
        mentions.append(f"{{{key}}}")
        substitution[key] = {
            "type": "mention",
            "mentionee": {
                "type": "user",
                "userId": s["userId"]
            }
        }

    mention_line = " ".join(mentions) if mentions else "-"

    display_text = (
        f"🚨 New Ticket Assigned {analysis.get('ritm', '-')}!\n"
        f"🎯 Route: {team_name}\n\n"
        f"{mention_line}"
    )

    payload = {
        "to": group_id,
        "messages": [
            {
                "type": "textV2",
                "text": display_text,
                "substitution": substitution
            },
            {
                "type": "flex",
                "altText": f"New Task: {analysis.get('task', '-')}",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "New Ticket Assigned!",
                                "weight": "bold",
                                "color": "#E74C3C",
                                "size": "md"
                            },
                            {
                                "type": "text",
                                "text": f"🔗 RITM: {analysis.get('ritm', '-')}",
                                "weight": "bold",
                                "size": "sm",
                                "margin": "lg"
                            },
                            {
                                "type": "text",
                                "text": f"📌 Task: {analysis.get('task', '-')}",
                                "size": "sm",
                                "margin": "xs",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"🚀 Route: {team_name}",
                                "weight": "bold",
                                "color": "#2980B9",
                                "size": "sm",
                                "margin": "md",
                                "wrap": True
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#27AE60",
                                "action": {
                                    "type": "message",
                                    "label": "✅ รับทราบเคสนี้",
                                    "text": f"รับทราบ | {analysis.get('task', '-')} | {analysis.get('ritm', '-')}"
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

    return payload


def build_daily_summary_payload(summary: dict, group_id: str):
    report_date = summary["report_date_th"]
    incident_count = summary["incident_count"]
    request_count = summary["request_count"]
    change_count = summary["change_count"]
    total_count = summary["total_count"]

    payload = {
        "to": group_id,
        "messages": [
            {
                "type": "flex",
                "altText": f"รายงานสรุปเคสประจำวัน {report_date}",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"รายงานสรุปเคสประจำวัน {report_date}",
                                "weight": "bold",
                                "size": "md",
                                "wrap": True
                            },
                            {"type": "separator", "margin": "md"},
                            {
                                "type": "text",
                                "text": "เคส Incident ที่เปิดทั้งหมด",
                                "weight": "bold",
                                "size": "sm",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": f"{incident_count} เคส",
                                "color": "#E74C3C",
                                "weight": "bold",
                                "size": "lg"
                            },
                            {
                                "type": "text",
                                "text": "เคส Request ที่ได้รับทั้งหมด",
                                "weight": "bold",
                                "size": "sm",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": f"{request_count} เคส",
                                "color": "#E74C3C",
                                "weight": "bold",
                                "size": "lg"
                            },
                            {
                                "type": "text",
                                "text": "เคส Change ที่ได้รับทั้งหมด",
                                "weight": "bold",
                                "size": "sm",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": f"{change_count} เคส",
                                "color": "#E74C3C",
                                "weight": "bold",
                                "size": "lg"
                            },
                            {"type": "separator", "margin": "lg"},
                            {
                                "type": "text",
                                "text": "รวมเคสทั้งสิ้น",
                                "weight": "bold",
                                "size": "sm",
                                "margin": "lg"
                            },
                            {
                                "type": "text",
                                "text": f"{total_count} เคส",
                                "color": "#E74C3C",
                                "weight": "bold",
                                "size": "xl"
                            }
                        ]
                    }
                }
            }
        ]
    }

    return payload