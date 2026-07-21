from dataclasses import dataclass
from datetime import date, datetime
import sqlite3
from typing import List, Optional


@dataclass
class BucketMonthTopUp:
    top_up_id: int
    month_start: Optional[str] = None
    start_amount: Optional[int] = None
    end_amount: Optional[int] = None

    bucket_id: Optional[int] = None
    bucket_name: Optional[str] = None