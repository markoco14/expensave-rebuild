""" Main application file """
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.router import router
from app.hv_router import hv_router

app = FastAPI()

app.include_router(router)
app.include_router(hv_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
