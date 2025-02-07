""" Main application file """
from datetime import datetime
from typing import Annotated
from fastapi import Depends, Request, APIRouter
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth import auth_service
from app.auth.auth_service import get_current_user
from app.core.database import get_db
from app.core import links
from app.services import winnings_service
from app.user.user_model import DBUser


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/totals")
def get_totals_page(
    request: Request,
        current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1
):
    """Returns the totals page where the user can view how much they spent on every given day."""


    if not current_user:
        context = {"request": request,
                   "nav_links": links.unauthenticated_navlinks}
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )
    limit = 10
    offset = (page - 1) * limit
    query = text(
        """
        SELECT 
            DATE(CONVERT_TZ(purchase_time, '+00:00', '+08:00')) as local_date,
            SUM(price) as total_spent,
            COUNT(*) as number_of_purchases
        FROM expense_transactions 
        WHERE user_id = :user_id
        GROUP BY local_date
        ORDER BY local_date DESC
        LIMIT :limit
        OFFSET :offset;
        """)

    query_results = db.execute(query, {"user_id": current_user.id, "limit": limit, "offset": offset})

    results_dict = []
    grand_total = 0
    for result in query_results:
        results_dict.append(result._asdict())
        if not result.total_spent == None:
            grand_total += result.total_spent

    winnings_year = datetime.now().year
    current_month = datetime.now().month
    winnings_period = winnings_service.get_winnings_period_by_month(month=current_month) 
    
    context = {
        "user": current_user,
        "request": request,
        "nav_links": links.authenticated_navlinks,
        "totals": results_dict,
        "grand_total": grand_total,
        "page": page,
        "limit": limit,
        "winnings_year": winnings_year,
        "winnings_period": winnings_period
    }
    return templates.TemplateResponse(
        name="/totals/index.html",
        context=context
    )
