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
from app.routers import purchases, totals_router, faker_router, receipts_router, winnings_router
from app.camera import camera_router
from app.services import transaction_service, winnings_service
from app.transaction import transaction_schemas
from app.transaction.transaction_model import Transaction
from app.user import user_schemas, user_service
from app.user.user_model import DBUser

settings = get_settings()

app = FastAPI()
app.include_router(purchases.router)
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
        name="home/index.html",
        context=context
    )


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

