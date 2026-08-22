import sqlite3


def list_with_top_ups(conn: sqlite3.Connection, month_start, user_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.category_id,
            c.name
        FROM category as c
        WHERE c.user_id = :user_id
        """,
        {"user_id": user_id}
        )

    categories = cursor.fetchall()

    return categories


def get_with_top_up(conn: sqlite3.Connection, month_start, bucket_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            b.bucket_id,
            b.name,
            b.is_daily,
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
