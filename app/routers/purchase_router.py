"""User authentication routes"""
from decimal import Decimal
import json
import os
from time import sleep
from typing import Annotated
from datetime import datetime, timedelta


import boto3
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
        if not purchase.items:
            purchase.items = "Items not recorded."
        if not purchase.location:
            purchase.location = "Location not recorded."
        if not purchase.currency:
            purchase.currency = "Currency not recorded."
        if not purchase.price:
            purchase.price = "Price not recorded."
        else: 
            purchase.price = f"${purchase.price:.2f}"

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
    purchase_time: Annotated[str, Form()] = None,
    lottery: Annotated[str, Form()] = None,
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
    
    db_today_purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)
    
    purchase_time_object = datetime.fromisoformat(purchase_time)
    utc_corrected_time = purchase_time_object - timedelta(hours=8)

    new_purchase = transaction_schemas.PurchaseCreate(
        user_id=current_user.id,
        items=items,
        price=price,
        currency=currency,
        location=location,
        receipt_lottery_number=lottery,
        purchase_time=utc_corrected_time,
        transaction_type=TransactionType.PURCHASE,
        payment_method=payment_method)

    db_purchase = Transaction(**new_purchase.model_dump())
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)

    if len(db_today_purchases) == 0:
        db_today_purchases.append(db_purchase)
        currency = "TWD"
        context = {
            "request": request,
            "currency": currency,
            "purchases": db_today_purchases,
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

    formatted_purchase_time = db_purchase.purchase_time.strftime("%Y-%m-%dT%H:%M:%S")
    db_purchase.formatted_purchase_time = formatted_purchase_time

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
    purchase_time: Annotated[str, Form()],
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

    purchase_time = datetime.fromisoformat(purchase_time)
    utc_purchase_time = purchase_time - timedelta(hours=8)

    db_purchase.purchase_time = utc_purchase_time
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


@router.delete("/purchases/{purchase_id}", response_class=HTMLResponse)
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
    # get the db purchase 
    db_purchase = db.query(Transaction).filter(
        Transaction.id == purchase_id
    ).first()

    # TODO: response not returning properly
    if not db_purchase:
        response = Response(
            status_code=404, content="Purchase not found.")
        return response

    # if no photos, delete purchase
    if not db_purchase.s3_key and not db_purchase.thumbnail_s3_key:
        try:
            db.delete(db_purchase)
            db.commit()
        except Exception as e:
            response = Response(
                status_code=501, content="Unable to delete purchase. Please try again.")
            return response
    else:
        # initialize s3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_DEFAULT_REGION")
        )

        # if photo, delete photo
        # try delete original
        keys_to_delete = []
        if db_purchase.s3_key:
            keys_to_delete.append({"Key": db_purchase.s3_key})
            
        # try delete thumbnail
        if db_purchase.thumbnail_s3_key:
            keys_to_delete.append({"Key": db_purchase.thumbnail_s3_key})

        try:
            response = s3.delete_objects(
                Bucket=os.environ.get("AWS_PROJECT_BUCKET"),
                Delete={
                    "Objects": keys_to_delete
                }
            )

            # Check for errors in the S3 response
            if 'Errors' in response:
                raise Exception("Unable to delete purchase photos. Please try again.")

            db_purchase.s3_key = None
            db_purchase.thumbnail_s3_key = None
            db.commit()
        except Exception as e:
            response = Response(
                status_code=501, content="Unable to delete purchase photos. Please try again.")
            return response
            
        # if photo deleted, delete purchase
        try:
            db.delete(db_purchase)
            db.commit()
        except IntegrityError:
            response = Response(
                status_code=501,
                content="Unable to delete purchase. Please try again."
            )

    # we don't need to calculate current day's total spending if request comes from "/purchases"
    # but we do if comes from "/"
    referer = request.headers.get("referer")
    if referer and "purchases" not in referer:
        db_purchases = transaction_service.get_user_today_purchases(
            current_user_id=current_user.id, db=db)

        # If the spending list is empty we need to refresh the content to empty list state
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
    
    # if request comes from "/purchases" we only need to send a response
    response = Response(status_code=200)
    
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
