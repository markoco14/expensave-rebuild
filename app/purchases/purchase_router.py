"""User authentication routes"""

from typing import Annotated
from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases import purchase_schemas, purchase_service
from app.purchases.purchase_model import DBPurchase

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/purchases")
def get_purchases_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
    ):
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            request=request,
            name="/website/web-home.html",
            context=context
        )
    
    purchases = db.query(DBPurchase).filter(
        DBPurchase.user_id == current_user.id,
        ).order_by(DBPurchase.purchase_time.desc()).all()
    
    for purchase in purchases:
        purchase.purchase_time = (purchase.purchase_time + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    
    headings = [
        "items", 
        "price", 
        "purchase_time", 
        "location", 
        "currency", 
        "actions"
    ]
    context={
        "nav_links": links.authenticated_navlinks,
        "headings": headings,
        "purchases": purchases
        }
    return templates.TemplateResponse(
        request=request,
        name="/app/purchases/purchases.html",
        context=context
    )


@router.post("/track-purchase")
def store_purchase(
    request: Request,
    items: Annotated[str, Form()],
    price: Annotated[Decimal, Form()],
    currency: Annotated[str, Form()],
    location: Annotated[str, Form()],
    db: Session = Depends(get_db),
    ):
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            request=request,
            name="/website/web-home.html",
            context=context
        )

    purchases = purchase_service.get_user_today_purchases(current_user_id=current_user.id, db=db)
    
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

    if len(purchases) == 0:
        purchases.append(db_purchase)
        currency = "TWD"
        context={
            "currency": currency,
            "purchases": purchases,
            "message": "Purchase tracked!"
            }
        return templates.TemplateResponse(
            headers={"HX-Trigger": "calculateTotalSpent"},
            request=request,
            name="app/home/spending-form-list-response.html",
            context=context
            )


    currency = "TWD"
    context={
        "currency": currency,
        "purchase": db_purchase,
        "message": "Purchase tracked!"
        }
    return templates.TemplateResponse(
        headers={"HX-Trigger": "calculateTotalSpent"},
        request=request,
        name="app/home/spending-form-row-response.html",
        context=context
        )


@router.delete("/delete-purchase/{purchase_id}", response_class=HTMLResponse)
def delete_purchase(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    purchase_id: int
    ):
    """Sign out a user"""
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            status_code=401,
            request=request,
            name="/website/web-home.html",
            context=context
        )
    
    try:
        db.query(DBPurchase).filter(
            DBPurchase.id == purchase_id
            ).delete()
        db.commit()
    except IntegrityError:
        response = Response(status_code=400, content="Unable to delete purchase. Please try again.")
        return response

    response = Response(status_code=200)
    return response


@router.get("/calculate-total-spent")
def calculate_total_sepnt(
    request: Request,
    db: Session = Depends(get_db)
    ):
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            request=request,
            name="/website/web-home.html",
            context=context
        )

    purchases = purchase_service.get_user_today_purchases(current_user_id=current_user.id, db=db)
    
    totalSpent = purchase_service.calculate_day_total_spent(purchases=purchases)

    return templates.TemplateResponse(
        request=request,
        name="app/home/total-spent-span.html",
        context={"totalSpent": totalSpent}
    )


@router.post("/validate-items")
def validate_items(request: Request, items: Annotated[str, Form()] = None):
    if not items:
        items = []
        return templates.TemplateResponse(
            request=request,
            name="app/home/item-tags.html",
            context={"items": items}
        )
    items.rstrip(" ")
    items = items.split(", ")
    return templates.TemplateResponse(
        request=request,
        name="app/home/item-tags.html",
        context={"items": items}
    )