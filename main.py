""" Main application file """
from datetime import datetime, time, timedelta

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

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
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            request=request,
            name="/website/web-home.html",
            context=context
        )
    
    start_of_day = time_service.get_utc_start_of_day(utc_offset=8)
    end_of_day = time_service.get_utc_end_of_day(utc_offset=8)
    
    purchases = db.query(DBPurchase).filter(
        DBPurchase.user_id == current_user.id,
        DBPurchase.purchase_time >= start_of_day,
        DBPurchase.purchase_time <= end_of_day
        ).order_by(DBPurchase.purchase_time.desc()).all()
    
    user_timezone = "Asia/Taipei" # replace with user's timezone one day
    purchases = time_service.adjust_purchase_dates_for_local_time(
        purchases=purchases, user_timezone=user_timezone)
    
    totalSpent = purchase_service.calculate_day_total_spent(purchases=purchases)

    currency = "TWD"
    context={"currency": currency,
             "nav_links": links.authenticated_navlinks,
             "purchases": purchases,
             "totalSpent": totalSpent,
            }
    return templates.TemplateResponse(
        request=request,
        name="app/app-home.html",
        context=context
    )

@app.get("/signup")
def get_sign_up_page(request: Request):
    context={"nav_links": links.unauthenticated_navlinks}
    return templates.TemplateResponse(
        request=request,
        name="website/signup.html",
        context=context
    )

@app.get("/signin")
def get_sign_in_page(request: Request):
    context={"nav_links": links.unauthenticated_navlinks}
    return templates.TemplateResponse(
        request=request,
        name="website/signin.html",
        context=context
    )
