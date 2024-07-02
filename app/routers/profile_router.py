"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases import purchase_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
def get_user_profile(
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
            name="/website/web-home.html",
            context=context
        )

    lifetime_spent = purchase_service.get_user_lifetime_spent(
        db=db, current_user_id=current_user.id
    )


    context = {
        "request": request,
        "user": current_user,
        "lifetime_spent": lifetime_spent
    }

    return templates.TemplateResponse(
        name="/app/profile/profile-page.html",
        context=context
    )
