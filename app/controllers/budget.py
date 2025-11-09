import sqlite3

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def create(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    form_data = await request.form()
    amount = form_data.get("amount")
    started_at = form_data.get("start_date")
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM budget WHERE user_id = ? AND ended_at IS NULL;", (request.state.user.user_id, ))
            
            current_budget = cursor.fetchone()
            if current_budget:
                cursor.execute("UPDATE budget SET ended_at = ? WHERE budget_id = ?;", (started_at, current_budget["budget_id"]))

            cursor.execute("INSERT INTO budget (amount, user_id, started_at) VALUES (?, ?, ?);", (amount, request.state.user.user_id, started_at))

            conn.commit()
        except Exception as e:
            print(f"something went wrong creating the budget: {e}")
            conn.rollback()

    return RedirectResponse(url="/me", status_code=303)
