""" Main application file """
from datetime import datetime


from fastapi import Depends, Request, APIRouter
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.core import time_service
from app.services import transaction_service


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
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

    purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)
    
    for purchase in purchases:
        purchase.purchase_time = time_service.format_taiwan_time(purchase_time=purchase.purchase_time)


    user_timezone = "Asia/Taipei"  # replace with user's timezone one day
    purchases = time_service.adjust_purchase_dates_for_local_time(
        purchases=purchases, user_timezone=user_timezone)

    totalSpent = transaction_service.calculate_day_total_spent(
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


@router.get("/signup")
def get_sign_up_page(request: Request):
    context = {"request": request, "nav_links": links.unauthenticated_navlinks}
    return templates.TemplateResponse(
        name="website/signup.html",
        context=context
    )


@router.get("/signin")
def get_sign_in_page(request: Request):
    context = {"request": request, "nav_links": links.unauthenticated_navlinks}
    return templates.TemplateResponse(
        name="website/signin.html",
        context=context
    )
