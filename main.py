""" Main application file """
from pprint import pprint
from datetime import datetime, time, timedelta

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth import auth_service, auth_router
from app.core.database import get_db
from app.core import links
from app.core import time_service
from app.purchases.purchase_model import DBPurchase
from app.purchases import purchase_router, purchase_service

app = FastAPI()
app.include_router(auth_router.router)
app.include_router(purchase_router.router)

templates = Jinja2Templates(directory="templates")


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
    context = {"request": request,
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
    context = {
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "totals": results_dict,
        "grand_total": grand_total
        }
    return templates.TemplateResponse(
        name="/app/totals/totals-page.html",
        context=context
    )
