from app.db.db_connection import db
from sqlalchemy import text
from app.constants.export_headers import (
    MASTER_DB_HEADERS,
    AUDIT_RAW_HEADERS,
)


# =========================================================
# 3) DB HELPERS
# =========================================================
def task_already_recorded(task_id):
    if not task_id:
        print("⚠️ task_already_recorded: task_id is empty")
        return False

    session = db.get_session()
    try:
        query = text("""
            SELECT record_id
            FROM email_ticket_master
            WHERE record_id = :record_id
            LIMIT 1
        """)

        result = session.execute(query, {"record_id": task_id}).fetchone()

        if result is not None:
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ DB check error for task {task_id}: {e}")
        return False
    finally:
        session.close()


def filter_columns(record: dict, allowed_columns: list):
    return {k: record.get(k) for k in allowed_columns}


def save_master_and_audit_record(master_record, audit_record):
    session = db.get_session()

    try:
        master_allowed_columns = list(MASTER_DB_HEADERS) + ["ml_confidence", "decision_mode"]
        master_data = filter_columns(master_record, master_allowed_columns)
        audit_data = filter_columns(audit_record, AUDIT_RAW_HEADERS)
        master_cols = ", ".join(master_data.keys())
        master_params = ", ".join([f":{k}" for k in master_data.keys()])
        audit_cols = ", ".join(audit_data.keys())
        audit_params = ", ".join([f":{k}" for k in audit_data.keys()])

        master_sql = f"""
        INSERT INTO email_ticket_master ({master_cols})
        VALUES ({master_params})
        """

        audit_sql = f"""
        INSERT INTO email_ticket_audit_raw ({audit_cols})
        VALUES ({audit_params})
        """

        session.execute(text(master_sql), master_data)
        session.execute(text(audit_sql), audit_data)
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"❌ DB Save Error for {master_record.get('record_id')}: {str(e)}")
        raise
    finally:
        session.close()