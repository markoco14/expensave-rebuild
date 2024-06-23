"""User authentication routes"""

from typing import Annotated

from decimal import Decimal

from fastapi import APIRouter, Depends, Request,Form

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases import purchase_schemas, purchase_service
from app.purchases.purchase_model import Transaction


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/track-purchase")
def store_purchase(
    request: Request,
    items: Annotated[str, Form()],
    price: Annotated[Decimal, Form()],
    currency: Annotated[str, Form()],
    location: Annotated[str, Form()],
    type: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/web-home.html",
            context=context
        )

    purchases = purchase_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    new_purchase = purchase_schemas.PurchaseCreate(
        user_id=current_user.id,
        items=items,
        price=price,
        currency=currency,
        location=location,
        type=type
    )

    db_purchase = Transaction(**new_purchase.model_dump())
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)

    if len(purchases) == 0:
        purchases.append(db_purchase)
        currency = "TWD"
        context = {
            "request": request,
            "currency": currency,
            "purchases": purchases,
            "message": "Purchase tracked!"
        }
        return templates.TemplateResponse(
            headers={"HX-Trigger": "calculateTotalSpent"},
            name="app/home/spending-form-list-response.html",
            context=context
        )

    currency = "TWD"
    context = {
        "request": request,
        "currency": currency,
        "purchase": db_purchase,
        "message": "Purchase tracked!"
    }
    return templates.TemplateResponse(
        headers={"HX-Trigger": "calculateTotalSpent"},
        name="app/home/spending-form-row-response.html",
        context=context
    )



@router.get("/calculate-total-spent")
def calculate_total_sepnt(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/web-home.html",
            context=context
        )

    purchases = purchase_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    totalSpent = purchase_service.calculate_day_total_spent(
        purchases=purchases)

    return templates.TemplateResponse(
        name="app/home/total-spent-span.html",
        context={
            "totalSpent": totalSpent,
            "request": request
        }
    )


@router.post("/validate-items")
def validate_items(request: Request, items: Annotated[str, Form()] = None):
    if not items:
        items = []
        return templates.TemplateResponse(
            name="app/home/item-tags.html",
            context={"items": items}
        )
    items.rstrip(" ")
    items = items.split(", ")
    return templates.TemplateResponse(
        name="app/home/item-tags.html",
        context={"items": items}
    )
