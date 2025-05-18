"""User authentication routes"""
from decimal import Decimal
import json
import os
import re
from typing import Annotated, Optional
from datetime import datetime, timedelta


import boto3
from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.auth.auth_service import get_current_user
from app.core.database import get_db
from app.core import links, time_service
from app.transaction import transaction_schemas
from app.transaction.transaction_model import Transaction, TransactionType
from app.core import time_service as TimeService
from app.services import transaction_service, winnings_service
from datetime import timedelta
from app import no_purchases_fake_data
from app.user.user_model import DBUser


router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/purchases")
def index(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1
):
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
    
    winnings_year = datetime.now().year
    current_month = datetime.now().month
    winnings_period = winnings_service.get_winnings_period_by_month(month=current_month) 

    context = {
        "user": current_user,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "headings": headings,
        "purchases": purchases,
        "fake_purchases": no_purchases_fake_data.example_purchases_data,
        "page": page,
        "winnings_year": winnings_year,
        "winnings_period": winnings_period
    }
    
    if request.headers.get("HX-Request"):
        if not request.query_params.get("page"):
            return templates.TemplateResponse(
                name="purchases/index.html",
                context=context
            )
        
        return block_templates.TemplateResponse(
            name="purchases/_rows.html",
            context=context,
        )
    
    return templates.TemplateResponse(
        name="purchases/index.html",
        context=context
    )

@router.get("/purchases/new")
def new(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    context = {"request": request, "user": current_user}

    response = templates.TemplateResponse(
        name="/purchases/new/index.html",
        context=context
    )

    return response


@router.post("/purchases", response_class=Response)
def store_new_purchase(
    request: Request,
    lottery_letters: Annotated[str, Form(...)],
    lottery_numbers: Annotated[str, Form(...)],
    date: Annotated[str, Form(...)],
    time: Annotated[str, Form(...)],
    amount: Annotated[str, Form(...)],
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Store a new purchase"""

    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    
    form_values = {
        "lottery_letters": lottery_letters,
        "lottery_numbers": lottery_numbers,
        "time": time,
        "amount": amount
    }

    form_errors = {}

    # validate lottery info
    if not lottery_letters and not lottery_numbers:
        form_errors["letters"] = "Lottery ID letters and numbers are required."
    elif not lottery_letters:
        form_errors["letters"] = "Lottery ID letters are required."
    elif not lottery_letters.isalpha():
        form_errors["letters"] = "Lottery ID letters must be A-Z."
    elif not lottery_letters.isupper():
        form_errors["letters"] = "Lottery ID letters must be uppercase."
    elif len(lottery_letters) < 2:
        form_errors["letters"] = "There needs to be 2 letters."
    elif len(lottery_letters) > 2:
        form_errors["letters"] = "There can only be 2 letters."
    elif not lottery_numbers:
        form_errors["numbers"] = "Lottery ID numbers are required."
    elif not lottery_numbers.isdigit():
        form_errors["numbers"] = "Lottery ID numbers must be 0-9."
    elif len(lottery_numbers) < 8:
        form_errors["numbers"] = "Lottery number must have at least 8 numbers"
    elif len(lottery_numbers) > 8:
        form_errors["numbers"] = "Lottery number must have at most 8 numbers"

    # in case somehow not a time
    if not time:
        form_errors["time"] = "Please enter a purchase time."
    
    if len(time.split(":")) < 3:
        form_errors["time"] = "Please enter a valid time."
        form_values["time"] = ""
    
    # validate amount
    if not amount:
        form_errors["amount"] = "Please enter a purchase amount."
    elif not amount.isdigit():
        form_errors["amount"] = "Amount must be a number greater than or equal to 0."
    elif int(amount) < 0:
        form_errors["amount"] = "Amount must not be less than 0"

    try:
        purchase_time_object = datetime.strptime(time, "%H:%M:%S").time()
    except ValueError:
        form_errors["time"] = "Please enter a valid time."

    if form_errors:
        response = templates.TemplateResponse(
            name="purchases/new/form.html",
            context={
                "request": request,
                "form_errors": form_errors,
                "form_values": form_values
                },
        )

        return response
    print(date)
    print(time)
    combined_purchase_time = f"{date} {time}"
    print(combined_purchase_time)
    # return "oK"
    print(time)
    purchase_time_object = datetime.strptime(combined_purchase_time, "%Y-%m-%d %H:%M:%S")
    print(purchase_time_object)
    utc_corrected_time = purchase_time_object - timedelta(hours=8)
    print(utc_corrected_time)

    if lottery_letters:
        final_lottery_number = f"{lottery_letters}-{lottery_numbers}"
    else:
        final_lottery_number = lottery_numbers
    
    # new_purchase = transaction_schemas.PurchaseCreateMinimal(
    #     user_id=current_user.id,
    #     price=amount,
    #     receipt_lottery_number=final_lottery_number,
    #     purchase_time=utc_corrected_time
    # )

    # db_purchase = Transaction(**new_purchase.model_dump())
    db_purchase = Transaction(
        user_id=current_user.id,
        price=amount,
        receipt_lottery_number=final_lottery_number,
        purchase_time=purchase_time_object
    )

    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)

    db_today_purchases = transaction_service.get_user_today_purchases(
        current_user_id=current_user.id, db=db)
    
    if len(db_today_purchases) == 0:
        db_today_purchases.append(db_purchase)
        context = {
            "request": request,
            "purchases": db_today_purchases,
            "message": "Purchase tracked!"
        }

        return templates.TemplateResponse(
            headers={"HX-Trigger": "calculateTotalSpent, getPurchaseList"},
            name="purchases/new/form.html",
            context=context
        )
    
    db_purchase.purchase_time = TimeService.format_taiwan_time(purchase_time=db_purchase.purchase_time)
    
    response = templates.TemplateResponse(
        name="purchases/new/form.html",
        headers={"HX-Trigger": "calculateTotalSpent, getPurchaseList"},
        context={
            "request": request,
            "form_errors": {},
            "form_values": {}
            },
    )

    return response



@router.get("/purchases/{purchase_id}")
def get_purchase_detail_row(
    request: Request,
    purchase_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
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
        "user": current_user,
        "purchase": db_purchase,
    }

    if request.headers.get("hx-request"):
        return block_templates.TemplateResponse(
            name="/app/spending-list-item.html",
            context=context,
            block_name="content"
        )

    return templates.TemplateResponse(
        name="/purchases/show/index.html",
        context=context
    )


@router.put("/purchases/{purchase_id}")
def update_purchase(
    request: Request,
    purchase_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    purchase_time: Annotated[str, Form()] = None,
    price: Annotated[Optional[str], Form()] = None,
    location: Annotated[Optional[str], Form()] = None,
    items: Annotated[Optional[str], Form()] = None,
    lottery: Annotated[Optional[str], Form()] = None,
    payment_method: Annotated[Optional[str], Form()] = None
):  
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
    price = Decimal(price) if price else None
    if price:
        db_purchase.price = price

    if location:
        db_purchase.location = location

    if items:
        db_purchase.items = items

    if purchase_time:
        purchase_time = datetime.fromisoformat(purchase_time)
        utc_purchase_time = purchase_time - timedelta(hours=8)
        db_purchase.purchase_time = utc_purchase_time

    if payment_method:
        db_purchase.payment_method = payment_method

    if lottery:
        db_purchase.receipt_lottery_number = lottery

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


@router.get("/purchases/{purchase_id}/edit")
def get_edit_purchase_form(
    request: Request,
    purchase_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    tab: str = "lottery",
):

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

    if not db_purchase.location:
        db_purchase.location = ""

    if not db_purchase.items:
        db_purchase.items = ""

    # correct date time
    db_purchase.purchase_time = TimeService.format_taiwan_time(
        purchase_time=db_purchase.purchase_time)

    formatted_purchase_time = db_purchase.purchase_time.strftime("%Y-%m-%dT%H:%M:%S")
    db_purchase.formatted_purchase_time = formatted_purchase_time

    if not db_purchase.receipt_lottery_number:
        db_purchase.receipt_lottery_number = ""

    context = {
        "request": request,
        "user": current_user,
        "purchase": db_purchase,
        "tab": tab
    }

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            name="purchases/edit/_form.html",
            context=context
        )
    
    response = templates.TemplateResponse(
        name="purchases/edit/index.html",
        context=context
    )

    return response


@router.get("/purchases/edit/form/{purchase_id}")
def get_form_for_lottery(
    request: Request,
    purchase_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    tab: str = "info",
):  
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )

    db_purchase = db.query(Transaction).filter(Transaction.id == purchase_id).first()
    context = {
        "request": request,
        "purchase": db_purchase,
        "tab": tab
    }

    if tab == "info":
        return templates.TemplateResponse(
            name="purchases/edit/inputs/edit-info.html",
            context=context
        )
    
    if tab == "time":
        # change from UTC to Taiwan time
        db_purchase.purchase_time += timedelta(hours=8)
        return templates.TemplateResponse(
            name="purchases/edit/inputs/edit-time.html",
            context=context
        )
    
    if tab == "lottery":
        return templates.TemplateResponse(
            name="purchases/edit/inputs/edit-lottery.html",
            context=context
        )

    if tab == "method":
        return templates.TemplateResponse(
            name="purchases/edit/inputs/edit-method.html",
            context=context
        )


@router.delete("/purchases/{purchase_id}", response_class=HTMLResponse)
def delete_purchase(
    request: Request,
    response: Response,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    purchase_id: int
):
    """Sign out a user"""
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
    if request.headers.get("hx-request"):
        response = Response(status_code=200)
        response.headers["hx-redirect"] = "/purchases"

        return response
        
    return RedirectResponse(status_code=200)


@router.get("/purchases/details/{date}")
def get_purchase_details_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    date: str,
):
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
        
    date_from_iso = datetime.fromisoformat(date)
    yesterday_from_iso = (date_from_iso - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_from_iso = (date_from_iso + timedelta(days=1)).strftime("%Y-%m-%d")

    context = {
        "user": current_user,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "purchases": purchases,
        "today_date": date,
        "yesterday_date": yesterday_from_iso,
        "tomorrow_date": tomorrow_from_iso,
    }

    if request.headers.get("HX-Request"):
        return block_templates.TemplateResponse(
            name="/purchases/day-list.html",
            context=context,
        )

    return templates.TemplateResponse(
        name="purchases/purchase-detail.html",
        context=context
    )



@router.get("/purchases/date/{selected_date}")
def get_updated_purchase_list(
    request: Request,
    selected_date: datetime,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    db_purchases = transaction_service.get_user_purchases_by_date(
                                            current_user_id=current_user.id, 
                                            selected_date=selected_date, 
                                            db=db
                                        )
    
    for purchase in db_purchases:
        purchase.purchase_time = time_service.format_taiwan_time(purchase_time=purchase.purchase_time)

    context = {
        "request": request,
        "today_date": selected_date,
        "purchases": db_purchases
    }

    return templates.TemplateResponse(
        name="/purchases/day-list.html",
        context=context
    )



@router.get("/purchases/totals/{selected_date}")
def calculate_total_spent(
    request: Request,
    selected_date: datetime,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )

    db_purchases = transaction_service.get_user_purchases_by_date(
                                            current_user_id=current_user.id, 
                                            selected_date=selected_date, 
                                            db=db
                                        )

    totalSpent = transaction_service.calculate_day_total_spent(
        purchases=db_purchases)

    return templates.TemplateResponse(
        name="app/total-spent-span.html",
        context={
            "totalSpent": totalSpent,
            "today_date": selected_date,
            "request": request
        }
    )


@router.post("/purchases/validate-items")
def validate_items(request: Request, items: Annotated[str, Form()] = None):
    if not items:
        items = []
        return templates.TemplateResponse(
            name="app/item-tags.html",
            context={"items": items}
        )
    items.rstrip(" ")
    items = items.split(", ")
    return templates.TemplateResponse(
        name="app/item-tags.html",
        context={"items": items}
    )
