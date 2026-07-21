import sqlite3


def list_for_period(user_id, period_start, period_end):
    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        purchase_rows = conn.execute(
            """
            SELECT * 
            FROM purchase 
            WHERE user_id = :user_id 
            AND purchased_at >= :period_start
            AND purchased_at < :period_end;""", 
            {
                "user_id": user_id, 
                "period_start": period_start.strftime('%Y-%m-%d %H:%M:%S'),
                "period_end": period_end.strftime('%Y-%m-%d %H:%M:%S')
            }
            ).fetchall()
        
        return purchase_rows
        
        
def list_for_bucket_and_month(conn: sqlite3.Connection, bucket_id: int, utc_month_start, utc_month_end):
    cursor = conn.cursor()
    
    cursor.execute("""
                    SELECT * 
                    FROM purchase 
                    WHERE bucket_id = ?
                    AND purchased_at >= ?
                    AND purchased_at < ?
                    ORDER BY purchased_at DESC;""", (bucket_id, utc_month_start, utc_month_end))
    
    purchase_rows = cursor.fetchall()

    return purchase_rows

def get_logged_spend_for_bucket_month(conn: sqlite3.Connection, bucket_id: int, utc_month_start, utc_month_end):
    cursor = conn.cursor()
    
    cursor.execute("""
                    SELECT TOTAL(amount) AS logged_spending
                    FROM purchase 
                    WHERE bucket_id = :bucket_id
                    AND purchased_at >= :utc_month_start
                    AND purchased_at < :utc_month_end;""",
                    {
                        "bucket_id": bucket_id,
                        "utc_month_start": utc_month_start,
                        "utc_month_end": utc_month_end
                    }
                )
    
    purchase_total = cursor.fetchone()

    return purchase_total["logged_spending"]