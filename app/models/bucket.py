from dataclasses import dataclass
from datetime import date, datetime
import sqlite3
from typing import List, Optional


@dataclass
class Bucket:
    bucket_id: int
    name: Optional[str] = None
    amount: Optional[int] = None
    is_daily: Optional[bool] = None
    month_start: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = None

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

    @classmethod
    def get(cls, conn: sqlite3.Connection, bucket_id: int):
        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, name FROM bucket WHERE bucket_id = ?;", (bucket_id, ))
        row = cursor.fetchone()
        return Bucket(**row) if row else None