from sqlalchemy import text
from app.db.db_connection import db

def was_job_run_today(job_name: str, date_str: str) -> bool:
    session = db.get_session()
    try:
        sql = text("SELECT last_run_date FROM worker_job_states WHERE job_name = :job_name")
        result = session.execute(sql, {"job_name": job_name}).fetchone()
        if result and str(result[0]) == date_str:
            return True
    except Exception as e:
        print(f"❌ DB Error in was_job_run_today: {e}")
    finally:
        session.close()
    return False

def mark_job_run_today(job_name: str, date_str: str):
    session = db.get_session()
    try:
        sql = text("""
            INSERT INTO worker_job_states (job_name, last_run_date, updated_at)
            VALUES (:job_name, :date_str, CURRENT_TIMESTAMP)
            ON CONFLICT (job_name)
            DO UPDATE SET last_run_date = EXCLUDED.last_run_date, updated_at = CURRENT_TIMESTAMP;
        """)
        session.execute(sql, {"job_name": job_name, "date_str": date_str})
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"❌ DB Error in mark_job_run_today: {e}")
    finally:
        session.close()