from datetime import date
from calendar import monthrange
import sqlite3
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")


async def create(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    if "daily" in request.url.path:
        is_daily = True
    else:
        is_daily = False
    
    form_data = await request.form()

    bucket_name = "Daily Spending" if is_daily else form_data.get("bucket")
    if not bucket_name:
        return "You need a bucket name"
    
    amount = form_data.get("amount")
    if not amount:
        return "You need a bucket amount"
    
    if not amount.isdigit():
        return "The amount needs to be a number"
    
    amount = int(amount)
    
    month_start = date.today().replace(day=1)

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        try:
            if is_daily:
                number_of_days = monthrange(month_start.year, month_start.month)[1]              
                monthly_amount = amount * number_of_days
                cursor.execute("INSERT INTO bucket (user_id, name, amount, month_start, is_daily) VALUES (?, ?, ?, ?, ?);", (request.state.user.user_id, bucket_name, monthly_amount, month_start, 1))
            else:
                cursor.execute("INSERT INTO bucket (user_id, name, amount, month_start) VALUES (?, ?, ?, ?);", (request.state.user.user_id, bucket_name, amount, month_start))
        except sqlite3.IntegrityError as e:
            message = str(e)
            if "UNIQUE constraint failed" in message:
                return f"You already have that bucket for this month."
            else:
                return f"Something went wrong storing that bucket."
        except Exception as e:
            print(e)
            return f"Something went wrong on our server."
    
    return RedirectResponse(url="/me", status_code=303)


def delete(request: Request, bucket_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, user_id FROM bucket WHERE bucket_id = ?;", (bucket_id,))

        bucket = cursor.fetchone()
        if not bucket:
            return "There is no bucket"

        if bucket["user_id"] != request.state.user.user_id:
            return "You are not the right user"
        
        cursor.execute("DELETE FROM bucket WHERE bucket_id = ?;", (bucket_id,))
    
    response = Response(status_code=204, headers={"hx-refresh": "true"})
    return response

