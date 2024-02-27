""" Main application file """

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service, auth_router
from app.core.database import get_db
from app.core import links
from app.purchases.purchase_model import DBPurchase
from app.purchases import purchase_router

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
    
    start_of_day = datetime.combine(
        datetime.now(), time.min) - timedelta(hours=8)
    end_of_day = datetime.combine(
        datetime.now(), time.max) - timedelta(hours=8)
    
    purchases = db.query(DBPurchase).filter(
        DBPurchase.user_id == current_user.id,
        DBPurchase.purchase_time >= start_of_day,
        DBPurchase.purchase_time <= end_of_day
        ).order_by(DBPurchase.purchase_time.desc()).all()
    

    taipei_time = ZoneInfo("Asia/Taipei")
    totalSpent = 0
    for purchase in purchases:
        purchase.purchase_time = purchase.purchase_time.astimezone(taipei_time)
        totalSpent += purchase.price

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
