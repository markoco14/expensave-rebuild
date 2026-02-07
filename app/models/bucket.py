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
    def list_for_month(cls, user_id: int, fields: List[str]):
        if not fields:
            columns = "bucket_id, name, is_daily"
        else:
            columns = ", ".join(fields).rstrip(", ")
        
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute(f"SELECT {columns} FROM bucket WHERE user_id = ?;", (user_id, ))
            
            return [Bucket(**row) for row in cursor.fetchall()]


    @classmethod
    def get_user_daily_bucket(cls, user_id: int, columns: List[str] = []) :
        if not columns:
            columns = "*"
        else:
            columns = ", ".join(columns).rstrip(",")

        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute(f"SELECT {columns} FROM bucket WHERE user_id = ? AND is_daily = 1;", (user_id, ))
            row = cursor.fetchone()

            return Bucket(**row) if row else None
