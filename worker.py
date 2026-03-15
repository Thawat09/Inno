import time
from datetime import datetime
from app.services.mail_service import fetch_and_group_tasks
from app.services.report_service import get_daily_case_summary
from app.services.line_service import send_task_notification, send_daily_summary_notification
from app.config import Config


def run_worker():
    print("🚀 Email Worker started...")
    last_summary_sent_key = None

    while True:
        try:
            now = datetime.now()
            print(f"🔍 Checking for new emails... ({now.strftime('%H:%M:%S')})")

            task_list = fetch_and_group_tasks()

            if not task_list:
                print("😴 No new tasks found.")
            else:
                for task_item in task_list:
                    print(f"📤 Sending notification for {task_item['task']}")
                    print(f"📌 Task: {task_item['task']} | Parent: {task_item['ritm']}")
                    print(f"🎯 Route To: {task_item['final_route']}")
                    # send_task_notification(task_item)
                    time.sleep(1)

            # ส่ง summary ทุกวันตอน 17:30 ครั้งเดียว
            now = datetime.now()
            # now = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0)
            if now.hour == 17 and now.minute == 30:
                today_key = now.strftime("%Y-%m-%d")

                if last_summary_sent_key != today_key:
                    summary = get_daily_case_summary()
                    print(
                        f"📊 Sending daily summary | "
                        f"Incident={summary['incident_count']} | "
                        f"Request={summary['request_count']} | "
                        f"Change={summary['change_count']} | "
                        f"Total={summary['total_count']}"
                    )
                    # send_daily_summary_notification(summary)
                    last_summary_sent_key = today_key

            print(f"✅ Cycle complete. Sleeping for {Config.CHECK_INTERVAL}s...")

        except Exception as e:
            print(f"⚠️ Worker Loop Error: {e}")

        time.sleep(Config.CHECK_INTERVAL)