"""User authentication routes"""
import os
from typing import Annotated


from fastapi import APIRouter, Depends, Request, Response, Form
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
import faker


from app.core.database import get_db
from app.services import faker_service


router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")

fake = faker.Faker()

@router.get("/generate-data", response_class=JSONResponse)
def create_fake_data(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    if not os.getenv("ENVIRONMENT") == "dev":
        return JSONResponse(content={"error": "This route is only available in development mode"}, status_code=403)
    
    try:
        faker_service.create_fake_data(db=db, user_id=1)
        return JSONResponse(content={"message": "Data generated"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

