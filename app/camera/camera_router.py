"""Camera feature routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core import links


router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/cam1")
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

    context = {
        "user": current_user,
        "request": request,
    }

    
    return templates.TemplateResponse(
        name="/camera/cam1.html",
        context=context
    )

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

    context = {
        "user": current_user,
        "request": request,
    }
    
    return templates.TemplateResponse(
        name="/camera/cam2.html",
        context=context
    )


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

    context = {
        "user": current_user,
        "request": request,
    }

    return templates.TemplateResponse(
        name="/camera/cam3.html",
        context=context
    )


