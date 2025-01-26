"""Camera feature routes"""
from io import BytesIO
import os
import time
from typing import Annotated

import boto3
from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from PIL import Image

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.transaction.transaction_model import Transaction
from app.background import camera_tasks
from app import utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/receipts")
def get_receipts_page(
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
    if not current_user.feature_camera:
        response = RedirectResponse(url="/", status_code=303)
        return response
    
    limit = 2
    offset = limit * (page - 1)
    
    dbTransactions = db.query(Transaction
                                ).filter(Transaction.s3_key != None
                                ).order_by(Transaction.purchase_time.desc()
                                ).limit(limit).offset(offset
                                ).all()
    
    if request.headers.get("HX-Request"):
        if not request.query_params.get("page"):
            response = templates.TemplateResponse(
            name="/camera/receipts.html",
            context={
                "request": request,
                "user": current_user,
                "transactions": dbTransactions,
                "page": page
                },
            status_code=200)
            return response
        
        response = templates.TemplateResponse(
            name="/camera/partials/receipt-list.html",
            context={
                "request": request,
                "user": current_user,
                "transactions": dbTransactions,
                "page": page
            },
            status_code=200)
        return response
    
    response = templates.TemplateResponse(
        name="/camera/receipts.html",
        context={
            "request": request,
            "user": current_user,
            "transactions": dbTransactions,
            "page": page
            },
        status_code=200)
    return response