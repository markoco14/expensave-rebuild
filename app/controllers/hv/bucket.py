import sqlite3
from types import SimpleNamespace
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.bucket import Bucket
from app.models.bucket_month_top_up import BucketMonthTopUp


templates = Jinja2Templates(directory="templates")

async def list(request: Request):
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bucket;")
        buckets = [Bucket(**row) for row in cursor.fetchall()]

        cursor.execute("""
                        SELECT 
                            btu.top_up_id,
                            btu.bucket_id,
                            btu.month_start,
                            btu.start_amount,
                            b.name as bucket_name 
                        FROM bucket_month_top_up as btu 
                        JOIN bucket as b 
                        USING (bucket_id);""")
        top_ups = [BucketMonthTopUp(**row) for row in cursor.fetchall()]
        
    
    print(top_ups)
    return templates.TemplateResponse(
        request=request,
        name="hv/bucket/index.xml",
        context={}
    )
