"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core import links


router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)
templates = Jinja2Templates(directory="templates")


@router.get("/")
def get_admin_page(
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
            name="/website/web-home.html",
            context=context
        )

    if not current_user.is_admin:
        user_data = {
            "display_name": current_user.display_name,
            "is_admin": current_user.is_admin,
        }
        context = {
            "user": user_data,
            "request": request,
        }

        # return RedirectResponse(url="/", status_code=401)
        return templates.TemplateResponse(
            name="/app/home/app-home.html",
            context=context,
        )

    user_data = {
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
    }
    context = {
        "user": user_data,
        "request": request,
    }
    return templates.TemplateResponse(
        name="/app/admin/admin-home.html",
        context=context
    )
