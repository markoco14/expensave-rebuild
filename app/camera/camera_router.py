"""Camera feature routes"""
from io import BytesIO
import os
import time
from typing import Annotated

import boto3
from fastapi import APIRouter, Depends, File, Request, UploadFile
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


@router.get("/camera")
def get_purchases_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
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

    context = {
        "user": current_user,
        "request": request,
    }

    
    return templates.TemplateResponse(
        name="/camera/index.html",
        context=context
    )

@router.post("/camera")
def upload_photo(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    photo: UploadFile = File(...)
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
    
    # upload to s3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION")
    )
    
    upload_time = round(time.time() * 1000)
    environment = os.environ.get("ENVIRONMENT")    
    image_key = utils.get_original_storage_string(
        user_id=current_user.id,
        environment=environment,
        upload_time=upload_time
    )

    try:
        s3.put_object(
            Bucket=os.environ.get("AWS_PROJECT_BUCKET"),
            Key=image_key,
            Body=photo.file.read()
        )
    except Exception as e:
        response = JSONResponse(
                status_code=303,
                content={"message": "Camera upload failed!"}
            )
        response.headers["hx-trigger"] = "cameraUploadFailed"
        return response
    
    # save the image in the database
    dbTransaction = Transaction(
        user_id=current_user.id,
        s3_key=image_key
    )
    try:
        db.add(dbTransaction)
        db.commit()
        db.refresh(dbTransaction)
    except Exception as e:
        response = JSONResponse(
                status_code=303,
                content={"message": "Failed to upload photo!"}
        )
        response.headers["hx-trigger"] = "cameraUploadFailed"
        return response
    
    if request.headers.get("HX-Request"):
            response = JSONResponse(
                status_code=303,
                content={"message": "Photo uploaded successfully!"}
            )

            response.headers["hx-trigger"] = "cameraUploadSuccess"
            return response
    
    context={
        "request": request,
        "user": current_user,
        "message": "Photo uploaded successfully!"
        }

    response = RedirectResponse(url="/camera", status_code=303)
    return response


@router.get("/receipts")
def get_purchase_with_image_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
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
    
    dbTransactions = db.query(Transaction).filter(Transaction.s3_key != None).all()

    response = templates.TemplateResponse(
        name="/camera/receipts.html",
        context={
            "request": request,
            "user": current_user,
            "transactions": dbTransactions
            },
        status_code=200)
    return response


@router.get("/receipts/{transaction_id}")
def get_receipt_image(
    request: Request,
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)]
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
    
    # requests to this page only happen to regular request.
    # Not by HTMX so no need to check for HX-Request header
    # So FastAPI RedirectResponse works fine here
    if not current_user.feature_camera:
        response = RedirectResponse(url="/", status_code=303)
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
            name="/camera/image-receipt.html",
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
        name="/camera/image-receipt.html",
        context=context,
        status_code=200
    )

    return response

@router.get("/cam2")
def get_purchases_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
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

    context = {
        "user": current_user,
        "request": request,
    }
    
    return templates.TemplateResponse(
        name="/camera/cam2.html",
        context=context
    )

@router.post("/cam2")
def upload_photo(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    photo: UploadFile = File(...)
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
    
    upload_dir = "./temp/images/raw/v2"
    os.makedirs(upload_dir, exist_ok=True)
    image = Image.open(BytesIO(photo.file.read()))

    try:
        image.save(f"{upload_dir}/{photo.filename}")
    except:
        response = JSONResponse(
                status_code=303,
                content={"message": "Camera upload failed!"}
            )

        response.headers["hx-trigger"] = "cameraUploadFailed"
        return response
    
    if request.headers.get("HX-Request"):
            response = JSONResponse(
                status_code=303,
                content={"message": "Photo uploaded successfully!"}
            )

            response.headers["hx-trigger"] = "cameraUploadSuccess"
            return response

    return templates.TemplateResponse(
        name="/app/camera/index.html",
        context={
            "request": request,
            "user": current_user,
            "message": "Photo uploaded successfully!"
        })


@router.get("/cam3")
def get_purchases_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
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

    context = {
        "user": current_user,
        "request": request,
    }

    return templates.TemplateResponse(
        name="/camera/cam3.html",
        context=context
    )


@router.post("/cam3")
def upload_photo(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    photo: UploadFile = File(...)
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
    
    upload_dir = "./temp/images/raw/v3"
    os.makedirs(upload_dir, exist_ok=True)
    image = Image.open(BytesIO(photo.file.read()))
    image = image.rotate(270)

    try:
        image.save(f"{upload_dir}/{photo.filename}")
    except:
        response = JSONResponse(
                status_code=303,
                content={"message": "Camera upload failed!"}
            )

        response.headers["hx-trigger"] = "cameraUploadFailed"
        return response
    
    if request.headers.get("HX-Request"):
            response = JSONResponse(
                status_code=303,
                content={"message": "Photo uploaded successfully!"}
            )

            response.headers["hx-trigger"] = "cameraUploadSuccess"
            return response

    return templates.TemplateResponse(
        name="/app/camera/index.html",
        context={
            "request": request,
            "user": current_user,
            "message": "Photo uploaded successfully!"
        })
