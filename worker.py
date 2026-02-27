import time
from datetime import datetime
from app.services.mail_service import fetch_and_group_tasks
from app.services.line_service import send_task_notification
from app.config import Config

def run_worker():
    print("🚀 Email Worker started...")
    while True:
        try:
            print(f"🔍 Checking for new emails... ({datetime.now().strftime('%H:%M:%S')})")
            
            # รับค่าเป็น List ของ Task ทั้งหมดที่เจอในรอบนั้น
            task_list = fetch_and_group_tasks()
            
            if not task_list:
                print("😴 No new tasks found.")
            else:
                # วนลูปส่งทีละตัวตามรายการใน List
                for task_item in task_list:
                    print(f"📤 Sending notification for {task_item['task']}")
                    print(f"📌 Task: {task_item['task']} | Parent: {task_item['ritm']}")
                    print(f"🎯 Route To: {task_item['final_route']}")
                    # send_task_notification(task_item)
                    time.sleep(1) # ป้องกัน LINE Spam

            print(f"✅ Cycle complete. Sleeping for {Config.CHECK_INTERVAL}s...")
        
        except Exception as e:
            print(f"⚠️ Worker Loop Error: {e}")
        
        time.sleep(Config.CHECK_INTERVAL)