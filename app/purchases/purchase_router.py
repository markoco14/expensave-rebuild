"""User authentication routes"""

from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases.purchase_model import DBPurchase

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.delete("/delete-purchase/{purchase_id}", response_class=HTMLResponse)
def delete_purchase(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    purchase_id: int
    ):
    """Sign out a user"""
    current_user = auth_service.get_current_user(db=db, cookies=request.cookies)
    if not current_user:
        context={"nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            status_code=401,
            request=request,
            name="landing-page.html",
            context=context
        )
    
    try:
        db.query(DBPurchase).filter(
            DBPurchase.id == purchase_id
            ).delete()
        db.commit()
    except IntegrityError:
        response = Response(status_code=400, content="Unable to delete purchase. Please try again.")
        return response

    response = Response(status_code=200)
    return response