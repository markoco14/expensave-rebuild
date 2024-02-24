""" Main application file """
from decimal import Decimal
from pprint import pprint
from typing import Annotated
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


@app.get("/")
def get_index_page(request: Request):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
        )
    
    currency = "TWD"
    context={"currency": currency}
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.get("/signup")
def get_sign_up_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
    )
@app.get("/signin")
def get_sign_in_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signin.html",
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

    new_purchase = purchase_schemas.PurchaseCreate(
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