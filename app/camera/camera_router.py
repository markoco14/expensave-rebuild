"""Camera feature routes"""
from datetime import datetime
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

from app.auth.auth_service import get_current_user
from app.core.database import get_db
from app.core import links
from app.services import winnings_service
from app.transaction.transaction_model import Transaction
from app import utils
from app.user.user_model import DBUser

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/camera")
def get_camera_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
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
    
    winnings_year = datetime.now().year
    current_month = datetime.now().month
    winnings_period = winnings_service.get_winnings_period_by_month(month=current_month) 

    context = {
        "user": current_user,
        "request": request,
        "winnings_year": winnings_year,
        "winnings_period": winnings_period
    }

    
    return templates.TemplateResponse(
        name="/camera/index.html",
        context=context
    )

@router.post("/camera")
def upload_photo(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    photo: UploadFile = File(...),
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





@router.get("/cam2")
def get_purchases_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
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
    current_user: Annotated[DBUser, Depends(get_current_user)],
    photo: UploadFile = File(...)
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
    current_user: Annotated[DBUser, Depends(get_current_user)],
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
    current_user: Annotated[DBUser, Depends(get_current_user)],
    photo: UploadFile = File(...)
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
