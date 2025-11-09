""" Main application file """
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.new_router import router

app = FastAPI()
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")
