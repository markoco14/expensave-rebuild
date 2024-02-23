""" Main application file """
from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/track-purchase")
def track_purchase(
    request: Request,
    items: Annotated[str, Form()],
    price: Annotated[str, Form()],
    currency: Annotated[str, Form()],
    location: Annotated[str, Form()]
    ):
    return templates.TemplateResponse("track-purchase-form.html", {"request": request})