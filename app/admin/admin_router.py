"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.user.user_model import DBUser


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
            name="/website/index.html",
            context=context
        )

    if not current_user.is_admin:
        context = {
            "user": current_user,
            "request": request,
        }

        # return RedirectResponse(url="/", status_code=401)
        return templates.TemplateResponse(
            name="/app/app-home.html",
            context=context,
        )

    context = {
        "user": current_user,
        "request": request,
    }
    return templates.TemplateResponse(
        name="/admin/admin-home.html",
        context=context
    )


@router.get("/users")
def read_admin_users_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a list of users for admin to review"""
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

    if not current_user.is_admin:
        context = {
            "user": current_user,
            "request": request,
        }

        # return RedirectResponse(url="/", status_code=401)
        return templates.TemplateResponse(
            name="/app/app-home.html",
            context=context,
        )


    db_users = db.query(DBUser).all()
    context = {
        "user": current_user,
        "request": request,
        "users": db_users
    }
    return templates.TemplateResponse(
        name="/admin/users.html",
        context=context
    )


@router.delete("/users/{user_id}")
def delete_user(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """Hard deletes a user and their data"""
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

    if not current_user.is_admin:
        context = {
            "user": current_user,
            "request": request,
        }

        # return RedirectResponse(url="/", status_code=401)
        return templates.TemplateResponse(
            name="/app/app-home.html",
            context=context,
        )
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    db.delete(db_user)
    db.commit()

    return Response(status_code=200)
