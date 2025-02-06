"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.auth_service import get_current_user
from app.core.database import get_db
from app.user.user_model import DBUser


router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)
templates = Jinja2Templates(directory="templates")


@router.get("")
def get_admin_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    ):
    context = {"request": request}
    
    if not current_user:
        if request.headers.get("HX-Request"):
            response = Response(status_code=303)
            response.headers["HX-Redirect"] = "/"
            return response
        return RedirectResponse(url="/", status_code=303)
    
    if not current_user.is_admin:
        if request.headers.get("HX-Request"):
            response = Response(status_code=303)
            response.headers["HX-Redirect"] = "/"
            return response
        return RedirectResponse(url="/", status_code=303)
    
    context["user"] = current_user
    
    return templates.TemplateResponse(
        name="/admin/admin-home.html",
        context=context
    )


@router.get("/users")
def read_admin_users_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    ):
    """Returns a list of users for admin to review"""    
    context = {"request": request}

    if not current_user:
        if request.headers.get("HX-Request"):
            response = Response(status_code=303)
            response.headers["HX-Redirect"] = "/"
            return response
        return RedirectResponse(url="/", status_code=303)
    
    if not current_user.is_admin:
        if request.headers.get("HX-Request"):
            response = Response(status_code=303)
            response.headers["HX-Redirect"] = "/"
            return response
        return RedirectResponse(url="/", status_code=303)

    context["user"] = current_user
    return templates.TemplateResponse(
        name="/admin/users.html",
        context=context
    )


@router.delete("/users/{user_id}")
def delete_user(
    request: Request,
    user_id: int,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Hard deletes a user and their data"""    
    if not current_user:
        if request.headers.get("HX-Request"):
            response = Response(status_code=303)
            response.headers["HX-Redirect"] = "/"
            return response
        return RedirectResponse(url="/", status_code=303)
    
    if not current_user.is_admin:
        if request.headers.get("HX-Request"):
            response = Response(status_code=303)
            response.headers["HX-Redirect"] = "/"
            return response
        return RedirectResponse(url="/", status_code=303)
    
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    db.delete(db_user)
    db.commit()

    return Response(status_code=204)
