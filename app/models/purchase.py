from dataclasses import dataclass
import sqlite3
from typing import Optional

@dataclass
class Purchase:
    purchase_id: int
    amount: Optional[int] = None
    currency: Optional[str] = None
    purchased_at: Optional[str] = None
    timezone: Optional[str] = None
    user_id: Optional[int] = None
    bucket_id: Optional[int] = None
    bucket_name: Optional[int] = None

    @classmethod
    def get_user_purchases(cls, conn: sqlite3.Connection, user_id: int):
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                purchase.purchase_id,
                purchase.amount, purchase.currency,
                purchase.purchased_at, purchase.timezone,
                purchase.user_id,
                purchase.bucket_id as bucket_id,
                bucket.name as bucket_name
            FROM purchase
            JOIN bucket USING (bucket_id)
            WHERE purchase.user_id = ?
            ORDER BY purchased_at DESC;
            """, (user_id, ))
        
        return [Purchase(**row) for row in cursor.fetchall()]
    
    @classmethod
    def get(cls, conn: sqlite3.Connection, purchase_id: int):
        cursor = conn.cursor()
        cursor.execute("""
                    SELECT purchase.purchase_id, purchase.amount,
                        purchase.currency, purchase.purchased_at,
                        purchase.timezone, purchase.user_id,
                        purchase.bucket_id as bucket_id,
                        bucket.name as bucket_name 
                    FROM purchase 
                    JOIN bucket USING (bucket_id) 
                    WHERE purchase.purchase_id = ?;""", (purchase_id, ))
        
        row = cursor.fetchone()
        return Purchase(**row) if row else None