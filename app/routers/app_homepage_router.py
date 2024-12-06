"""User authentication routes"""

from typing import Annotated

from decimal import Decimal

from fastapi import APIRouter, Depends, Request, Form

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases import purchase_schemas
from app.purchases.transaction_model import Transaction, TransactionType
from app.services import transaction_service
from app.core import time_service as TimeService


router = APIRouter()
templates = Jinja2Templates(directory="templates")\




@router.post("/validate-items")
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
