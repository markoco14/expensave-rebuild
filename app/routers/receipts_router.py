"""Camera feature routes"""
from datetime import datetime
from io import BytesIO
import os
from typing import Annotated

import boto3
from fastapi import APIRouter, Depends, File, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session

from app.auth.auth_service import get_current_user
from app.core.database import get_db
from app.core import links
from app.services import winnings_service
from app.transaction.transaction_model import Transaction
from app.background import camera_tasks
from app import utils
from app.user.user_model import DBUser

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/receipts")
def get_receipts_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1
    ):

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
    
    winnings_year = datetime.now().year
    current_month = datetime.now().month
    winnings_period = winnings_service.get_winnings_period_by_month(month=current_month) 
    
    context = {
        "request": request,
        "user": current_user,
        "transactions": dbTransactions,
        "page": page,
        "winnings_year": winnings_year,
        "winnings_period": winnings_period
    }
    
    if request.headers.get("HX-Request"):
        if not request.query_params.get("page"):
            response = templates.TemplateResponse(
            name="/camera/receipts.html",
            context=context,
            status_code=200)
            return response
        
        response = templates.TemplateResponse(
            name="/camera/partials/receipt-list.html",
            context=context,
            status_code=200)
        return response
    
    response = templates.TemplateResponse(
        name="/camera/receipts.html",
        context=context,
        status_code=200)
    return response



@router.get("/receipts/images/thumbnail/{transaction_id}")
def get_receipt_thumbnail_image(
    request: Request,
    transaction_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ):

    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    
    # images are requested by htmx
    # need to handle with htmx redirect
    if not current_user.feature_camera:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = "/"
        return response
    
    dbTransaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    # boto3 client needs to be initialized in any case
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION")
    )

    # speed things up if thumbnail already exists
    if dbTransaction.thumbnail_s3_key:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ.get("AWS_PROJECT_BUCKET"),
                "Key": dbTransaction.thumbnail_s3_key
            },
            ExpiresIn=3600
        )

        context = {
            "request": request,
            "user": current_user,
            "presigned_url": presigned_url,
            "transaction": dbTransaction
        }
        
        return templates.TemplateResponse(
            name="/camera/partials/image-thumbnail.html",
            context=context
        )

    # s3_get_original_start = time.time()
    try:
        s3_response = s3.get_object(
            Bucket=os.environ.get("AWS_PROJECT_BUCKET"),
            Key=dbTransaction.s3_key
        )
    except Exception as e:
        print(f"Error fetching image from S3: {e}")
    # s3_get_original_end = time.time()
    # print(f"S3 fetch time: {s3_get_original_end - s3_get_original_start}")
    
    # image name in /thumbnail should match /original
    thumbnail_key = utils.get_thumbnail_storage_string(original_storage_string=dbTransaction.s3_key)
    quality = 90

    # resize_start_time = time.time()
    image_data = s3_response['Body'].read()
    thumbnail_photo = camera_tasks.create_thumbnail(image_data)
    # resize_end_time = time.time()
    # print(f"Resize time: {resize_end_time - resize_start_time}")
    
    # Save the thumbnail to an in-memory byte stream
    # upload_thumbnail_start = time.time()
    img_byte_arr = BytesIO()
    thumbnail_photo.save(img_byte_arr, format="JPEG", quality=quality)
    img_byte_arr.seek(0)  # Reset the stream's position to the beginning
    
    # upload thumbnail to s3
    try:
        s3.put_object(
                Bucket=os.environ.get("AWS_PROJECT_BUCKET"),
                Key=thumbnail_key,
                Body=img_byte_arr.getvalue(),
                ContentType="image/jpeg"
            )
    except Exception as e:
        print(f"Error uploading thumbnail to S3: {e}")
    # upload_thumbnail_end = time.time()
    # print(f"Thumbnail upload time: {upload_thumbnail_end - upload_thumbnail_start}")

    # generate presigned URL
    # get_presigned_url_start = time.time()
    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ.get("AWS_PROJECT_BUCKET"),
                "Key": thumbnail_key
            },
            ExpiresIn=3600
        )
        print(f"Presigned URL generated: {presigned_url}")
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
    # get_presigned_url_end = time.time()
    # print(f"Presigned URL generation time: {get_presigned_url_end - get_presigned_url_start}")

    # store in DB
    try:
        dbTransaction.thumbnail_s3_key = thumbnail_key
        db.commit()
    except Exception as e:
        print(f"Error storing thumbnail key in DB: {e}")

    context = {
        "request": request,
        "user": current_user,
        "presigned_url": presigned_url,
        "transaction": dbTransaction
    }

    response = templates.TemplateResponse(
        name="/camera/partials/image-thumbnail.html",
        context=context,
        status_code=200
    )

    return response



@router.get("/receipts/images/edit/{transaction_id}")
def get_receipt_edit_image(
    request: Request,
    transaction_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ):

    
    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    
    dbTransaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    # boto3 client needs to be initialized in any case
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION")
    )

    if dbTransaction.edit_view_s3_key:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ.get("AWS_PROJECT_BUCKET"),
                "Key": dbTransaction.edit_view_s3_key
            },
            ExpiresIn=3600
        )

        context = {
            "request": request,
            "user": current_user,
            "presigned_url": presigned_url,
            "transaction": dbTransaction
        }
        
        return templates.TemplateResponse(
            name="/camera/partials/image-edit.html",
            context=context
        )
    
    # s3_get_original_start = time.time()
    # try to fetch the original image from S3
    try:
        s3_response = s3.get_object(
            Bucket=os.environ.get("AWS_PROJECT_BUCKET"),
            Key=dbTransaction.s3_key
        )
    except Exception as e:
        print(f"Error fetching image from S3: {e}")

     # s3_get_original_end = time.time()
    # print(f"S3 fetch time: {s3_get_original_end - s3_get_original_start}")
    
    # image name in /edit should match /original
    edit_view_key = utils.get_edit_view_storage_string(original_storage_string=dbTransaction.s3_key)
    quality = 90

    # resize_start_time = time.time()
    image_data = s3_response['Body'].read()
    edit_view_photo = camera_tasks.create_edit_view(image_data)
    # resize_end_time = time.time()
    # print(f"Resize time: {resize_end_time - resize_start_time}")
    
    # Save the edit_view to an in-memory byte stream
    # upload_thumbnail_start = time.time()
    img_byte_arr = BytesIO()
    edit_view_photo.save(img_byte_arr, format="JPEG", quality=quality)
    img_byte_arr.seek(0)  # Reset the stream's position to the beginning

    # upload edit_view to s3
    try:
        s3.put_object(
                Bucket=os.environ.get("AWS_PROJECT_BUCKET"),
                Key=edit_view_key,
                Body=img_byte_arr.getvalue(),
                ContentType="image/jpeg"
            )
    except Exception as e:
        print(f"Error uploading thumbnail to S3: {e}")
    # upload_thumbnail_end = time.time()
    # print(f"Thumbnail upload time: {upload_thumbnail_end - upload_thumbnail_start}")

    # generate presigned URL
    # get_presigned_url_start = time.time()
    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ.get("AWS_PROJECT_BUCKET"),
                "Key": edit_view_key
            },
            ExpiresIn=3600
        )
        print(f"Presigned URL generated: {presigned_url}")
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
    # get_presigned_url_end = time.time()
    # print(f"Presigned URL generation time: {get_presigned_url_end - get_presigned_url_start}")

    
    # store in DB
    try:
        dbTransaction.edit_view_s3_key = edit_view_key
        db.commit()
    except Exception as e:
        print(f"Error storing thumbnail key in DB: {e}")

    context = {
        "request": request,
        "user": current_user,
        "presigned_url": presigned_url,
        "transaction": dbTransaction
    }

    response = templates.TemplateResponse(
        name="/camera/partials/image-edit.html",
        context=context,
        status_code=200
    )

    return response