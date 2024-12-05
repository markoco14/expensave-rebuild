""" Main application file """
import os
import time

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.admin import admin_router
from app.auth import auth_router
from app.core.config import get_settings
from app.routers import purchase_router, web_homepage_router, app_homepage_router, totals_router, faker_router

settings = get_settings()

app = FastAPI()
app.include_router(auth_router.router)
app.include_router(purchase_router.router)
app.include_router(admin_router.router)
app.include_router(web_homepage_router.router)
app.include_router(app_homepage_router.router)
app.include_router(totals_router.router)
app.include_router(faker_router.router)

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

