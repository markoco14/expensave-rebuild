"""User authentication routes"""
from decimal import Decimal
import json
from time import sleep
from typing import Annotated
from datetime import timedelta


from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.transaction import transaction_schemas
from app.transaction.transaction_model import Transaction, TransactionType
from app.core import time_service as TimeService
from app.services import transaction_service
from datetime import timedelta
from app import no_purchases_fake_data


router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/purchases")
def get_purchases_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    page: int = 1
):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )

    purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.PURCHASE
    ).order_by(Transaction.purchase_time.desc()).offset(10 * (page - 1)).limit(10).all()

    for purchase in purchases:
        purchase.purchase_time = (purchase.purchase_time + timedelta(hours=8))

    headings = [
        "items",
        "price",
        "date",
        "time",
        "location",
        "currency",
        "actions"
    ]


    context = {
        "user": current_user,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "headings": headings,
        "purchases": purchases,
        "fake_purchases": no_purchases_fake_data.example_purchases_data,
        "page": page
    }

    if request.headers.get("HX-Request"):
        return block_templates.TemplateResponse(
            name="/app/purchases/purchase-table-rows.html",
            context=context,
        )
    
    return templates.TemplateResponse(
        name="/app/purchases/index.html",
        context=context
    )



@router.post("/purchases")
def store_purchase(
    request: Request,
    items: Annotated[str, Form()],
    price: Annotated[Decimal, Form()],
    currency: Annotated[str, Form()],
    location: Annotated[str, Form()],
    payment_method: Annotated[str, Form()],
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
            name="/website/index.html",
            context=context
        )

    purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    new_purchase = transaction_schemas.PurchaseCreate(
        user_id=current_user.id,
        items=items,
        price=price,
        currency=currency,
        location=location,
        transaction_type=TransactionType.PURCHASE,
        payment_method=payment_method)

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
            headers={"HX-Trigger": "calculateTotalSpent, getPurchaseList"},
            name="app/purchases/new-purchase-form.html",
            context=context
        )

    db_purchase.purchase_time = TimeService.format_taiwan_time(purchase_time=db_purchase.purchase_time)

    currency = "TWD"
    context = {
        "request": request,
        "currency": currency,
        "purchase": db_purchase,
        "message": "Purchase tracked!"
    }
    
    # TODO: can't change to blocks just yet because
    # sending form as response with oob row
    return templates.TemplateResponse(
        headers={"HX-Trigger": "calculateTotalSpent"},
        name="app/home/spending-form-oob-response.html",
        context=context
    )

@router.get("/purchases/details")
def get_purchase_details_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date: str,
):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    year = int(date.split("-")[0])
    month = int(date.split("-")[1])
    day = int(date.split("-")[2])

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

    for purchase in purchases:
        purchase.purchase_time = TimeService.format_taiwan_time(
            purchase_time=purchase.purchase_time)

    context = {
        "user": current_user,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "purchases": purchases,
        "today_date": date,
    }

    if request.headers.get("HX-Request"):
        return block_templates.TemplateResponse(
            name="/app/home/spending-list.html",
            context=context,
        )

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
            name="/website/index.html",
            context=context
        )

    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()

    # correct date time
    db_purchase.purchase_time = TimeService.format_taiwan_time(
        purchase_time=db_purchase.purchase_time)

    db_purchase.date = TimeService.format_date_for_date_input(
        purchase_time=db_purchase.purchase_time)
    db_purchase.time = db_purchase.purchase_time.strftime("%H:%M:%S")

    context = {
        "request": request,
        "purchase": db_purchase,
    }

    return block_templates.TemplateResponse(
        name="/app/home/spending-list-item.html",
        context=context,
        block_name="content"
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
            name="/website/index.html",
            context=context
        )

    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()

    # correct date time
    db_purchase.purchase_time = TimeService.format_taiwan_time(
        purchase_time=db_purchase.purchase_time)

    db_purchase.date = TimeService.format_date_for_date_input(
        purchase_time=db_purchase.purchase_time)
    db_purchase.time = db_purchase.purchase_time.strftime("%H:%M:%S")

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
    date: Annotated[str, Form()],
    time: Annotated[str, Form()],
    payment_method: Annotated[str, Form()],
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
            name="/website/index.html",
            context=context
        )
    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()
    db_purchase.price = price
    db_purchase.location = location
    db_purchase.items = items

    adjusted_time_str = TimeService.format_incoming_date_and_time_utc(
        date=date, time=time)

    db_purchase.purchase_time = adjusted_time_str
    db_purchase.payment_method = payment_method
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
            name="/website/index.html",
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

    db_purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    if len(db_purchases) == 0:
        response = Response(
            status_code=200,
            headers={
                "HX-Trigger": "calculateTotalSpent, getPurchaseList"
            },)
        return response

    response = Response(
        status_code=200,
        headers={
            "HX-Trigger": "calculateTotalSpent"
        },)
    return response


@router.get("/purchase-list")
def get_updated_purchase_list(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)

    db_purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    for purchase in db_purchases:
        purchase.purchase_time = TimeService.format_taiwan_time(
            purchase_time=purchase.purchase_time)

    context = {
        "request": request,
        "purchases": db_purchases
    }
    return templates.TemplateResponse(
        name="/app/home/spending-list.html",
        context=context
    )



@router.get("/purchases/daily-total")
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
            name="/website/index.html",
            context=context
        )

    purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)

    totalSpent = transaction_service.calculate_day_total_spent(
        purchases=purchases)

    return templates.TemplateResponse(
        name="app/home/total-spent-span.html",
        context={
            "totalSpent": totalSpent,
            "request": request
        }
    )


@router.post("/purchases/validate-items")
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
