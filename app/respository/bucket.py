import sqlite3

from app.models.bucket import Bucket


def list_with_top_ups(conn: sqlite3.Connection, month_start, user_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            b.bucket_id,
            b.name,
            btu.start_amount,
            btu.end_amount,
            btu.month_start,
            btu.top_up_id
        FROM bucket as b
        JOIN bucket_month_top_up as btu
        USING (bucket_id)
        WHERE btu.month_start = :month_start
        AND b.user_id = :user_id;
        """,
        {"month_start": month_start, "user_id": user_id}
        )

    buckets = cursor.fetchall()
    
    return buckets
