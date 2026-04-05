import os
import time
import threading
from datetime import datetime
import schedule
from app.config import Config
from app.services.mail_service import fetch_and_group_tasks
from app.services.report_service import get_daily_case_summary
from app.services.line_service import (
    send_task_notification,
    send_daily_summary_notification,
)
from app.services.escalation_service import process_pending_escalations
from app.services.job_state_service import was_job_run_today, mark_job_run_today

# =========================================================
# CONFIG DEFAULTS
# =========================================================
ENABLE_LINE_SEND = str(getattr(Config, "ENABLE_LINE_SEND", "false")).lower() == "true"
EMAIL_POLL_INTERVAL_SECONDS = int(getattr(Config, "CHECK_INTERVAL", 10))
ESCALATION_CHECK_INTERVAL_SECONDS = int(getattr(Config, "ESCALATION_CHECK_INTERVAL", 60))
DAILY_SUMMARY_TIME = getattr(Config, "DAILY_SUMMARY_TIME", "17:30")
WORKER_IDLE_SLEEP_SECONDS = float(getattr(Config, "WORKER_IDLE_SLEEP_SECONDS", 1.0))


# =========================================================
# IN-PROCESS LOCKS
# =========================================================
_email_job_lock = threading.Lock()
_escalation_job_lock = threading.Lock()
_summary_job_lock = threading.Lock()


# =========================================================
# HELPERS
# =========================================================
def log(message: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")


def safe_run(job_name: str, fn):
    try:
        log(f"▶ START {job_name}")
        fn()
        log(f"✅ END {job_name}")
    except Exception as e:
        log(f"❌ ERROR {job_name}: {e}")


def _send_line_task(task_item: dict):
    if not ENABLE_LINE_SEND:
        log(
            f"LINE disabled (dry-run) | task={task_item.get('task')} "
            f"| ritm={task_item.get('ritm')} | route={task_item.get('final_route')}"
        )
        return

    status_code = send_task_notification(task_item)
    if status_code != 200:
        log(
            f"⚠ LINE send failed | task={task_item.get('task')} "
            f"| ritm={task_item.get('ritm')} | status={status_code}"
        )


def _send_line_summary(summary: dict):
    if not ENABLE_LINE_SEND:
        log(
            "LINE disabled (dry-run) | daily summary "
            f"| total={summary.get('total_count', 0)}"
        )
        return

    status_code = send_daily_summary_notification(summary)
    if status_code != 200:
        log(f"⚠ LINE daily summary failed | status={status_code}")


# =========================================================
# JOB 1: EMAIL POLLING
# =========================================================
def email_polling_job():
    if not _email_job_lock.acquire(blocking=False):
        log("⏭ Skip email polling: previous run still in progress")
        return

    try:
        log("🔍 Checking for new emails...")
        task_list = fetch_and_group_tasks()

        if not task_list:
            log("😴 No new tasks found.")
            return

        log(f"📥 New tasks found: {len(task_list)}")

        for idx, task_item in enumerate(task_list, start=1):
            task = task_item.get("task", "-")
            ritm = task_item.get("ritm", "-")
            route = task_item.get("final_route", "-")

            log(f"📌 [{idx}/{len(task_list)}] task={task} | ritm={ritm} | route={route}")

            #! _send_line_task(task_item)

            time.sleep(0.3)

    finally:
        _email_job_lock.release()


# =========================================================
# JOB 2: ESCALATION CHECK
# =========================================================
def escalation_check_job():
    if not _escalation_job_lock.acquire(blocking=False):
        log("⏭ Skip escalation check: previous run still in progress")
        return

    try:
        result = process_pending_escalations(
            max_rounds=3,
            default_wait_minutes=15,
            enable_line_send=ENABLE_LINE_SEND,
        )
        log(
            f"📈 Escalation checked | scanned={result['scanned']} "
            f"| escalated={result['escalated']} | closed={result['closed']}"
        )
    finally:
        _escalation_job_lock.release()


# =========================================================
# JOB 3: DAILY SUMMARY
# =========================================================
def daily_summary_job():
    if not _summary_job_lock.acquire(blocking=False):
        log("⏭ Skip daily summary: previous run still in progress")
        return

    try:
        today_key = datetime.now().strftime("%Y-%m-%d")

        if was_job_run_today("daily_summary", today_key):
            log(f"⏭ Daily summary already sent for {today_key}")
            return

        summary = get_daily_case_summary()

        log(
            "📊 Daily summary prepared "
            f"| incident={summary.get('incident_count', 0)} "
            f"| request={summary.get('request_count', 0)} "
            f"| change={summary.get('change_count', 0)} "
            f"| total={summary.get('total_count', 0)}"
        )

        _send_line_summary(summary)

        mark_job_run_today("daily_summary", today_key)

    finally:
        _summary_job_lock.release()


# =========================================================
# SCHEDULER BOOTSTRAP
# =========================================================
def register_jobs():
    schedule.every(EMAIL_POLL_INTERVAL_SECONDS).seconds.do(
        lambda: safe_run("email_polling_job", email_polling_job)
    )

    schedule.every(ESCALATION_CHECK_INTERVAL_SECONDS).seconds.do(
        lambda: safe_run("escalation_check_job", escalation_check_job)
    )

    schedule.every().day.at(DAILY_SUMMARY_TIME).do(
        lambda: safe_run("daily_summary_job", daily_summary_job)
    )

    log(
        "🧩 Jobs registered "
        f"| email_poll={EMAIL_POLL_INTERVAL_SECONDS}s "
        f"| escalation_check={ESCALATION_CHECK_INTERVAL_SECONDS}s "
        f"| daily_summary={DAILY_SUMMARY_TIME} "
        f"| enable_line_send={ENABLE_LINE_SEND}"
    )


def run_worker():
    log("🚀 Python Worker started")
    register_jobs()

    while True:
        schedule.run_pending()
        time.sleep(WORKER_IDLE_SLEEP_SECONDS)


if __name__ == "__main__":
    run_worker()