""" Main application file """
from datetime import datetime

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth import auth_service, auth_router
from app.core.database import get_db
from app.core import links
from app.core import time_service
from app.purchases import purchase_router, purchase_service
from app.admin import admin_router
import os
import time

app = FastAPI()
app.include_router(auth_router.router)
app.include_router(purchase_router.router)
app.include_router(admin_router.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class SleepMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if os.getenv("ENVIRONMENT") == "dev":
            SLEEP_TIME = 1
            print(f"development environment detecting, sleeping for {SLEEP_TIME} seconds")
            time.sleep(SLEEP_TIME)  # Delay for 3000ms (3 seconds)
        await self.app(scope, receive, send)


app.add_middleware(SleepMiddleware)


@app.get("/")
def get_index_page(request: Request, db: Session = Depends(get_db)):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {"request": request,
                   "nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            name="/website/web-home.html",
            context=context
        )

    purchases = purchase_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    user_timezone = "Asia/Taipei"  # replace with user's timezone one day
    purchases = time_service.adjust_purchase_dates_for_local_time(
        purchases=purchases, user_timezone=user_timezone)

    totalSpent = purchase_service.calculate_day_total_spent(
        purchases=purchases)

    currency = "TWD"
    user_data = {
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
    }

    today_date = datetime.now()

    context = {
        "user": user_data,
        "request": request,
        "today_date": today_date,
        "currency": currency,
        "nav_links": links.authenticated_navlinks,
        "purchases": purchases,
        "totalSpent": totalSpent,
    }
    return templates.TemplateResponse(
        name="app/home/app-home.html",
        context=context
    )


@app.get("/signup")
def get_sign_up_page(request: Request):
    context = {"request": request, "nav_links": links.unauthenticated_navlinks}
    return templates.TemplateResponse(
        name="website/signup.html",
        context=context
    )


@app.get("/signin")
def get_sign_in_page(request: Request):
    context = {"request": request, "nav_links": links.unauthenticated_navlinks}
    return templates.TemplateResponse(
        name="website/signin.html",
        context=context
    )


@app.get("/totals")
def get_totals_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Returns the totals page where the user can view how much they spent on every given day."""

    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {"request": request,
                   "nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            name="/website/web-home.html",
            context=context
        )

    query = text(
        """
        SELECT 
            SUM(price) as total_spent,
            DATE(purchase_time) as purchase_date,
            COUNT(*) as number_of_purchases,
            GROUP_CONCAT(items) as items_list
        FROM expense_purchases 
        WHERE user_id = :user_id
        GROUP BY DATE(purchase_time)
        """)
    query_results = db.execute(query, {"user_id": current_user.id})
    results_dict = []
    grand_total = 0
    for result in query_results:
        results_dict.append(result._asdict())
        grand_total += result.total_spent
    user_data = {
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
    }
    context = {
        "user": user_data,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "totals": results_dict,
        "grand_total": grand_total
    }
    return templates.TemplateResponse(
        name="/app/totals/totals-page.html",
        context=context
    )
