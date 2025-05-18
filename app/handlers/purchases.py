"""User authentication routes"""
import os
from typing import Annotated

import boto3
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth.auth_service import get_current_user
from app.core.database import get_db
from app.transaction.transaction_model import Transaction
from app.services import transaction_service
from app.user.user_model import DBUser


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def delete_purchase(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    purchase_id: int
    ):
    if not current_user:
        context = {
            "request": request,
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
        
    return RedirectResponse(url="/purchases", status_code=303)
