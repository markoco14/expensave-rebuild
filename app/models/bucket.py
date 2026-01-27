from dataclasses import dataclass
from datetime import date, datetime
import sqlite3
from typing import List

@dataclass
class Bucket:
    bucket_id: int
    name: str = None
    amount: int = None
    is_daily: bool = None
    month_start: date = None
    created_at: datetime = None
    updated_at: datetime = None
    user_id: int = None

    @classmethod
    def list_for_month(cls, month_start: str, user_id: int, fields: List[str]):
        if not fields:
            columns = "bucket_id, name, amount, is_daily"
        else:
            columns = ", ".join(fields).rstrip(", ")
        
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute(f"SELECT {columns} FROM bucket WHERE month_start = ? AND user_id = ?;", (month_start, user_id))
            return [Bucket(**row) for row in cursor.fetchall()]


