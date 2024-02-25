""" Main application file """
from decimal import Decimal
from pprint import pprint
from typing import Annotated
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service, auth_router
from app.core.database import get_db
from app.purchases import purchase_schemas
from app.purchases.purchase_model import DBPurchase

app = FastAPI()
app.include_router(auth_router.router)

templates = Jinja2Templates(directory="templates")

unauthenticated_navlinks = [
    {"text": "Home", "target": "/"},
    {"text": "Sign In", "target": "/signin"},
    {"text": "Sign Up", "target": "/signup"}
    ]

authenticated_navlinks = [
    {"text": "Home", "target": "/"},
    {"text": "Sign Out", "target": "/signout"}
    ]


@app.get("/")
def get_index_page(request: Request, db: Session = Depends(get_db)):
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": unauthenticated_navlinks}
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            context=context
        )
    
    start_of_day = datetime.combine(datetime.now(), time.min)
    end_of_day = datetime.combine(datetime.now(), time.max)
    
    purchases = db.query(DBPurchase).filter(
        DBPurchase.user_id == current_user.id,
        DBPurchase.purchase_time >= start_of_day,
        DBPurchase.purchase_time <= end_of_day
        ).order_by(DBPurchase.purchase_time.desc()).all()
    taipei_time = ZoneInfo("Asia/Taipei")

    for purchase in purchases:
        purchase.purchase_time = purchase.purchase_time.astimezone(taipei_time)
        print(purchase.purchase_time)

    currency = "TWD"
    context={"currency": currency,
             "nav_links": authenticated_navlinks,
             "purchases": purchases
            }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.get("/signup")
def get_sign_up_page(request: Request):
    context={"nav_links": unauthenticated_navlinks}
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context=context
    )
@app.get("/signin")
def get_sign_in_page(request: Request):
    context={"nav_links": unauthenticated_navlinks}
    return templates.TemplateResponse(
        request=request,
        name="signin.html",
        context=context
    )

@app.post("/track-purchase")
def track_purchase(
    request: Request,
    items: Annotated[str, Form()],
    price: Annotated[Decimal, Form()],
    currency: Annotated[str, Form()],
    location: Annotated[str, Form()],
    db: Session = Depends(get_db),
    ):
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": unauthenticated_navlinks}
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            context=context
        )

    new_purchase = purchase_schemas.PurchaseCreate(
        user_id=current_user.id,
        items=items,
        price=price,
        currency=currency,
        location=location
    )

    db_purchase = DBPurchase(**new_purchase.model_dump())
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)

    currency = "TWD"
    context={"currency": currency, "message": "Purchase tracked!"}
    return templates.TemplateResponse(
        request=request,
        name="track-purchase-form.html",
        context=context
        )