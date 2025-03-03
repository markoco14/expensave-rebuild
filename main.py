""" Main application file """
from datetime import datetime, timedelta
import os
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request, Response
from fastapi.responses import Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.admin import admin_router
from app.auth import auth_schemas, auth_service, session_service
from app.auth.auth_service import get_current_user
from app.core import time_service
from app.core.config import get_settings
from app.core.database import get_db
from app.routers import purchase_router, totals_router, faker_router, receipts_router, winnings_router
from app.camera import camera_router
from app.services import transaction_service, winnings_service
from app.transaction import transaction_schemas
from app.transaction.transaction_model import Transaction
from app.user import user_schemas, user_service
from app.user.user_model import DBUser

settings = get_settings()

app = FastAPI()
app.include_router(purchase_router.router)
app.include_router(admin_router.router)
app.include_router(totals_router.router)
app.include_router(faker_router.router)
app.include_router(camera_router.router)
app.include_router(receipts_router.router)
app.include_router(winnings_router.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def return_404_middleware(request: Request, call_next):
    """ Middleware to return 404 page if route not found """
    response = await call_next(request)
    if response.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return response

class SleepMiddleware:
    """ Middleware to sleep requests in development environment to similate slow network"""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if os.getenv("ENVIRONMENT") == "dev":
            print(
                f"development environment detecting, sleeping for {settings.SLEEP_TIME} seconds")
            time.sleep(settings.SLEEP_TIME)  # Delay for 3000ms (3 seconds)
        await self.app(scope, receive, send)


app.add_middleware(SleepMiddleware)



@app.get("/", response_class=templates.TemplateResponse)
def get_index_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    ):
    if not current_user:
        context = {"request": request}
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    
    return RedirectResponse(url="/date/{}".format(datetime.now().strftime("%Y-%m-%d")))


@app.get("/date/{selected_date}", response_class=templates.TemplateResponse)
def get_app_index_page(
    request: Request,
    selected_date: datetime,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ):
    if not current_user:
        context = {"request": request}
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    
    db_purchases = transaction_service.get_user_purchases_by_date(
                                            current_user_id=current_user.id, 
                                            selected_date=selected_date, 
                                            db=db
                                        )
    
    for purchase in db_purchases:
        purchase.purchase_time = time_service.format_taiwan_time(purchase_time=purchase.purchase_time)

    totalSpent = transaction_service.calculate_day_total_spent(
        purchases=db_purchases)
    
    yesterday_date = selected_date - timedelta(days=1)
    tomorrow_date = selected_date + timedelta(days=1)
    
    current_time = datetime.time(datetime.now())

    form_values = {
        "time": current_time.strftime("%I:%M:%S")
    }

    winnings_year = datetime.now().year
    current_month = datetime.now().month
    winnings_period = winnings_service.get_winnings_period_by_month(month=current_month) 

    context = {
        "request": request,
        "user": current_user,
        "today_date": selected_date,
        "yesterday_date": yesterday_date.strftime("%Y-%m-%d"),
        "tomorrow_date": tomorrow_date.strftime("%Y-%m-%d"),
        "purchases": db_purchases,
        "totalSpent": totalSpent,
        "form_values": form_values,
        "winnings_year": winnings_year,
        "winnings_period": winnings_period
    }

    return templates.TemplateResponse(
        name="app/index.html",
        context=context
    )


@app.post("/date/{selected_date}", response_class=templates.TemplateResponse)
def store_new_purchase(
    request: Request,
    selected_date: datetime,
    lottery_letters: Annotated[str, Form(...)],
    lottery_numbers: Annotated[str, Form(...)],
    time: Annotated[str, Form(...)],
    amount: Annotated[str, Form(...)],
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Store a new purchase"""
    if not current_user:
        context = {
            "request": request,
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
    
    # first check whether the lottery number has at least 8 digits
    # digit_regex = r"(\d+)"
    # lottery_numbers = lottery_numbers.upper()
    # digit_match = re.search(digit_regex, lottery_numbers)

    # try:
    #     lottery_digits = digit_match.group()
    # except AttributeError:
    #     lottery_digits = None

    # # validate lotttery number is at least 8 digits
    # if not lottery_digits:
    #     form_errors["lottery"] = "Please enter a valid lottery number."
    # elif len(lottery_digits) != 8:
    #     form_errors["lottery"] = "Lottery number must be 8 digits digits."

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
    

    # Convert the time string to a time object
    try:
        purchase_time_object = datetime.strptime(time, "%H:%M:%S").time()
    except ValueError:
        form_errors["time"] = "Please enter a valid time."

    if form_errors:
        response = templates.TemplateResponse(
            name="purchases/form/new.html",
            context={
                "request": request,
                "today_date": selected_date,
                "form_errors": form_errors,
                "form_values": form_values
                },
        )

        return response
    
    utc_corrected_time = datetime.combine(selected_date, purchase_time_object) - timedelta(hours=8)

    if lottery_letters:
        final_lottery_number = f"{lottery_letters}-{lottery_numbers}"
    else:
        final_lottery_number = lottery_numbers
    
    new_purchase = transaction_schemas.PurchaseCreateMinimal(
        user_id=current_user.id,
        price=amount,
        receipt_lottery_number=final_lottery_number,
        purchase_time=utc_corrected_time
    )

    db_purchase = Transaction(**new_purchase.model_dump())
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)

    db_purchases = transaction_service.get_user_purchases_by_date(
                                            current_user_id=current_user.id, 
                                            selected_date=selected_date, 
                                            db=db
                                        )
    
    # corrent the time for UI
    db_purchase.purchase_time = time_service.format_taiwan_time(purchase_time=db_purchase.purchase_time)
    
    if len(db_purchases) == 0:
        db_purchases.append(db_purchase)
        context = {
            "request": request,
            "today_date": selected_date,
            "purchases": db_purchases,
            "form_errors": {},
            "form_values": {
                "time": datetime.now().time().strftime("%I:%M:%S")
            },
            "message": "Purchase tracked!"
        }

        return templates.TemplateResponse(
            headers={"HX-Trigger": "calculateTotalSpent, getPurchaseList"},
            name="purchases/form/new.html",
            context=context
        )
    
    response = templates.TemplateResponse(
        name="purchases/form/new.html",
        headers={"HX-Trigger": "calculateTotalSpent, getPurchaseList"},
        context={
            "request": request,
            "today_date": selected_date,
            "form_errors": {},
            "form_values": {
                "time": datetime.now().time().strftime("%I:%M:%S")
            }
            },
    )

    return response


@app.get("/signup", response_class=templates.TemplateResponse)
def get_sign_up_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)]
    ):
    if not current_user:
        context = {"request": request}
        return templates.TemplateResponse(
            name="website/signup.html",
            context=context
        )
    
    return RedirectResponse(url="/date/{}".format(datetime.now().strftime("%Y-%m-%d")))


@app.post("/signup", response_class=Response)
def signup(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Sign up a user"""
    email = username
    # check if user exists
    existing_user = user_service.get_user_by_email(db=db, email=email)
    if existing_user:
        response = Response(status_code=400, content="Invalid email or password")
        return response

    # Hash password
    hashed_password = auth_service.get_password_hash(password)
    
    # create new user with encrypted password
    new_user = user_schemas.CreateUserHashed(email=email, hashed_password=hashed_password)
    db_user = user_service.create_user(db=db, user=new_user)

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()
    new_session = auth_schemas.CreateUserSession(
        session_id=session_cookie,
        user_id=db_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # store user session
    session_service.create_session(db=db, session=new_session)
    
    response = Response(status_code=200)
    response.set_cookie(
        key="session-id",
        value=session_cookie,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    response.headers["HX-Redirect"] = "/date/{}".format(datetime.now().strftime("%Y-%m-%d"))

    return response

@app.get("/signin", response_class=templates.TemplateResponse)
def get_sign_in_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)]
    ):
    if not current_user:
        context = {"request": request}
        return templates.TemplateResponse(
            name="website/signin.html",
            context=context
        )
    
    return RedirectResponse(url="/date/{}".format(datetime.now().strftime("%Y-%m-%d")))


@app.post("/signin", response_class=Response)
def signin(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Sign in a user"""
    # check if user exists
    email = username
    db_user = user_service.get_user_by_email(db=db, email=email)
    if not db_user:
        response = Response(status_code=400, content="Invalid email or password")
        return response

    # verify the password
    if not auth_service.verify_password(
        plain_password=password,
        hashed_password=db_user.hashed_password
        ):
        response = Response(status_code=400, content="Invalid email or password")
        return response

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()

    new_session = auth_schemas.CreateUserSession(
        session_id=session_cookie,
        user_id=db_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # store user session
    session_service.create_session(db=db, session=new_session)
    
    response = Response(status_code=200)
    response.set_cookie(
        key="session-id",
        value=session_cookie,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    response.headers["HX-Redirect"] = "/date/{}".format(datetime.now().strftime("%Y-%m-%d"))
    return response


@app.get("/signout", response_class=Response or RedirectResponse)
def signout(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
    ):
    """Sign out a user"""
    session_id = request.cookies.get("session-id")
    
    if session_id:
        session_service.destroy_session(db=db, session_id=session_id)

    if request.headers.get("HX-Request"):
        response = Response(status_code=303)
        response.delete_cookie(key="session-id")
        response.headers["HX-Redirect"] = "/"
        return response

    response = RedirectResponse(status_code=303, url="/")
    response.delete_cookie(key="session-id")

    return response

