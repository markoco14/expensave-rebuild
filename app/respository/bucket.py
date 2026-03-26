import sqlite3


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
        WHERE b.user_id = :user_id
        AND btu.month_start = :month_start;
        """,
        {"month_start": month_start, "user_id": user_id}
        )

    buckets = cursor.fetchall()

    return buckets


def get_with_top_up(conn: sqlite3.Connection, month_start, bucket_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            b.bucket_id,
            b.name,
            btu.top_up_id,
            btu.month_start,
            btu.start_amount,
            btu.end_amount
        FROM bucket AS b
        JOIN bucket_month_top_up AS btu
        USING (bucket_id)
        WHERE b.bucket_id = :bucket_id
        AND btu.month_start = :month_start;
        """,
        {"bucket_id": bucket_id, "month_start": month_start})
    
    bucket_top_up_join = cursor.fetchone()

    return bucket_top_up_join
