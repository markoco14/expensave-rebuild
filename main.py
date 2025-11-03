""" Main application file """
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import new_router

app = FastAPI()
app.include_router(new_router.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
