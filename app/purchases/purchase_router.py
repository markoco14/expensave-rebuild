"""User authentication routes"""
import json
from typing import Annotated
from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases import purchase_schemas, purchase_service
from app.purchases.purchase_model import Transaction
from app.core import time_service as TimeService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/purchases")
def get_purchases_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
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

    purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
    ).order_by(Transaction.purchase_time.desc()).all()

    for purchase in purchases:
        purchase.date = (purchase.purchase_time +
                         timedelta(hours=8)).strftime("%b %d")
        purchase.time = (purchase.purchase_time +
                         timedelta(hours=8)).strftime("%H:%M")

    headings = [
        "items",
        "price",
        "date",
        "time",
        "location",
        "currency",
        "actions"
    ]
    user_data = {
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
    }
    context = {
        "user": user_data,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "headings": headings,
        "purchases": purchases
    }
    return templates.TemplateResponse(
        name="/app/purchases/purchases.html",
        context=context
    )


@router.get("/purchases/{today_date}")
def get_purchase_details_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    today_date: str
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
    year = int(today_date.split("-")[0])
    month = int(today_date.split("-")[1])
    day = int(today_date.split("-")[2])
    start_of_day = TimeService.get_utc_start_of_current_day(
        year=year,
        month=month,
        day=day,
        utc_offset=8
    )
    end_of_day = TimeService.get_utc_end_of_current_day(
        year=year,
        month=month,
        day=day,
        utc_offset=8
    )

    purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.purchase_time >= start_of_day,
        Transaction.purchase_time <= end_of_day
    ).order_by(Transaction.purchase_time.desc()).all()

    user_data = {
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
    }

    context = {
        "user": user_data,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "purchases": purchases
    }
    return templates.TemplateResponse(
        name="/app/purchases/purchase-detail.html",
        context=context
    )


@router.get("/purchases/details/{purchase_id}")
def get_purchase_detail_row(
    request: Request,
    purchase_id: int,
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

    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()

    context = {
        "request": request,
        "purchase": db_purchase,
    }

    return templates.TemplateResponse(
        name="/app/purchases/purchase-detail-row.html",
        context=context
    )


@router.get("/purchases/details/edit/{purchase_id}")
def get_edit_purchase_form(
    request: Request,
    purchase_id: int,
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

    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()

    context = {
        "request": request,
        "purchase": db_purchase,
    }

    return templates.TemplateResponse(
        name="/app/purchases/edit-purchase-form.html",
        context=context
    )


@router.put("/purchases/details/edit/{purchase_id}")
def update_purchase(
    request: Request,
    purchase_id: int,
    price: Annotated[float, Form()],
    location: Annotated[str, Form()],
    items: Annotated[str, Form()],
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

    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()

    db_purchase.price = price
    db_purchase.location = location
    db_purchase.items = items
    db.commit()
    db.refresh(db_purchase)
    response = {
        'message': 'Purchase updated successfully!'
    }

    update_success_event = json.dumps({"notifyUser": response['message']})

    return JSONResponse(
        status_code=200,
        content=response,
        headers={"HX-Trigger": update_success_event}
    )


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


@router.delete("/delete-purchase/{purchase_id}", response_class=HTMLResponse)
def delete_purchase(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    purchase_id: int
):
    """Sign out a user"""
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            status_code=401,
            name="/website/web-home.html",
            context=context
        )

    try:
        db.query(Transaction).filter(
            Transaction.id == purchase_id
        ).delete()
        db.commit()
    except IntegrityError:
        response = Response(
            status_code=400, content="Unable to delete purchase. Please try again.")
        return response

    response = Response(status_code=200)
    return response


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
