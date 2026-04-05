from sqlalchemy import text
from app.db.db_connection import db


def get_staffs_by_team(team_name: str):
    session = db.get_session()
    try:
        # กรณีพิเศษ: GCP & AWS Team (Both)
        # ดึงคนแรกของ GCP Team 1 คน + AWS Team 1 คน
        if team_name == "GCP & AWS Team (Both)":
            sql = text("""
                WITH ranked AS (
                    SELECT
                        u.line_user_id,
                        lu.display_name,
                        u.sub_team,
                        u.created_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY u.sub_team
                            ORDER BY u.created_at ASC, u.id ASC
                        ) AS rn
                    FROM users u
                    INNER JOIN line_users lu
                        ON lu.user_id = u.line_user_id
                    WHERE u.is_active = 1
                        AND NULLIF(u.line_user_id, '') IS NOT NULL
                        AND u.sub_team IN ('GCP Team', 'AWS Team')
                )
                SELECT
                    display_name,
                    line_user_id
                FROM ranked
                WHERE rn = 1
                ORDER BY sub_team
            """)

            results = session.execute(sql).mappings().all()

            return [
                {
                    "name": row["display_name"],
                    "userId": row["line_user_id"]
                }
                for row in results
            ]

        # กรณีทั่วไป:
        # หา sub_team ก่อน
        # ถ้าไม่มี ค่อยหา main_team
        sql = text("""
            WITH candidate AS (
                SELECT
                    lu.display_name,
                    u.line_user_id,
                    u.created_at
                FROM users u
                INNER JOIN line_users lu
                    ON lu.user_id = u.line_user_id
                WHERE u.is_active = 1
                    AND NULLIF(u.line_user_id, '') IS NOT NULL
                    AND u.sub_team = :team_name
                ORDER BY u.created_at ASC, u.id ASC
                LIMIT 1
            ),
            fallback_candidate AS (
                SELECT
                    lu.display_name,
                    u.line_user_id,
                    u.created_at
                FROM users u
                INNER JOIN line_users lu
                    ON lu.user_id = u.line_user_id
                WHERE u.is_active = 1
                    AND NULLIF(u.line_user_id, '') IS NOT NULL
                    AND u.main_team = :team_name
                ORDER BY u.created_at ASC, u.id ASC
                LIMIT 1
            )
            SELECT display_name, line_user_id
            FROM candidate

            UNION ALL

            SELECT display_name, line_user_id
            FROM fallback_candidate
            WHERE NOT EXISTS (SELECT 1 FROM candidate)
        """)

        results = session.execute(sql, {
            "team_name": team_name
        }).mappings().all()

        return [
            {
                "name": row["display_name"],
                "userId": row["line_user_id"]
            }
            for row in results
        ]

    finally:
        session.close()