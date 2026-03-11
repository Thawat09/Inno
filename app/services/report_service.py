from datetime import datetime, timedelta
from app.db.db_connection import db
from sqlalchemy import text


def get_daily_case_summary():
    now = datetime.now()

    end_dt = now.replace(hour=17, minute=30, second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=1)

    report_date = end_dt
    report_date_th = report_date.strftime("%d/%m/") + str(report_date.year + 543)

    session = db.get_session()
    try:
        sql = text("""
            SELECT
                SUM(CASE WHEN ticket_type = 'incident_task' THEN 1 ELSE 0 END) AS incident_count,
                SUM(CASE WHEN ticket_type = 'catalog_task' THEN 1 ELSE 0 END) AS request_count,
                SUM(CASE WHEN ticket_type = 'change_task' THEN 1 ELSE 0 END) AS change_count,
                COUNT(*) AS total_count
            FROM email_ticket_master
            WHERE email_date >= :start_dt
              AND email_date < :end_dt
        """)

        result = session.execute(sql, {
            "start_dt": start_dt,
            "end_dt": end_dt
        }).mappings().first()

        incident_count = int(result["incident_count"] or 0)
        request_count = int(result["request_count"] or 0)
        change_count = int(result["change_count"] or 0)
        total_count = int(result["total_count"] or 0)

        return {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "report_date_th": report_date_th,
            "incident_count": incident_count,
            "request_count": request_count,
            "change_count": change_count,
            "total_count": total_count,
        }

    finally:
        session.close()