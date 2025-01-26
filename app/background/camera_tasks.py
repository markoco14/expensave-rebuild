from io import BytesIO
import os

import boto3
from fastapi import UploadFile
from PIL import Image


def optimize_for_web(photo: UploadFile = None, image_key: str = None):
    # Photo received from camera endpoint
    # Optimize the image
    file_path = "/home/mark/projects/savemoney/temp/images/raw/v1/1-1735892306039.png"
    original_photo = Image.open(file_path)
    
    edit_view_size = (500, 500)
    quality = 90
    edit_view_path = f"/home/mark/projects/savemoney/temp/images/optimized/edit/v1/1-1735892306039-{quality}.jpg"
    edit_view_photo = original_photo.copy()
    edit_view_photo.thumbnail(edit_view_size)
    edit_view_photo.save(edit_view_path, format="JPEG", quality=quality, optimize=True)

    # Upload the image to S3    
    # "/images/optimized/{image_key}"

    # Store image key in the DB

    # print success

    # no return necessary, not interacting with users
    pass

def optimize_with_thumbnail(photo: UploadFile = None, image_key: str = None):
    file_path = "/home/mark/projects/savemoney/temp/images/raw/v1/1-1735892306039.png"
    original_photo = Image.open(file_path)
    quality = 90

    thumbnail_size = (256, 256)
    thumbnail_path = f"/home/mark/projects/savemoney/temp/images/optimized/thumbnail/v1/1-1735892306039-{quality}.jpg"
    thumbnail_photo = original_photo.copy()
    thumbnail_photo.thumbnail(thumbnail_size)
    thumbnail_photo.save(thumbnail_path, format="JPEG", quality=quality, optimize=True)
    # Upload the image to S3    
    # "/images/optimized/{image_key}"

    # Store image key in the DB

    # print success

    # no return necessary, not interacting with users
    
    return thumbnail_photo

def create_thumbnail(image_data) -> Image:
    with Image.open(BytesIO(image_data)) as in_memory_image:
        thumbnail_size = (256, 256)
        thumbnail_photo = in_memory_image.copy()
        thumbnail_photo.thumbnail(thumbnail_size)
        thumbnail_photo = thumbnail_photo.rotate(270)
    
    return thumbnail_photo


def create_edit_view(image_data) -> Image:
    with Image.open(BytesIO(image_data)) as in_memory_image:
        edit_view_size = (500, 500)
        edit_view_photo = in_memory_image.copy()
        edit_view_photo.thumbnail(edit_view_size)
        edit_view_photo = edit_view_photo.rotate(270)

    return edit_view_photo