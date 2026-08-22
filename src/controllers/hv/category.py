import calendar
from datetime import datetime, timezone
import sqlite3
from typing import Annotated
from zoneinfo import ZoneInfo
from fastapi import Depends, Request, Response
from fastapi.templating import Jinja2Templates

from src.models.bucket import Bucket
from src.models.bucket_month_top_up import BucketMonthTopUp
from src.respository.category import get_with_top_up, list_with_top_ups
from src.respository import purchase_repository as purchase_repo
from src.config import get_db
from src.dependencies import is_user
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

async def list(
        request: Request, 
        conn: Annotated[sqlite3.Connection, Depends(get_db)]
        ):
    current_user = request.state.user
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    month_start = local_date_today.replace(day=1).date()
    
    try:
        category_rows = list_with_top_ups(conn=conn, month_start=month_start, user_id=current_user.user_id)
    except Exception as e:
        logger.error(f"DB error getting categories: {e}", exc_info=True)
        return Response(status_code=500, content="something went wrong on our end")
    
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/index.xml",
        context={
            "categories": category_rows,
            "current_month": month_start
            }
        )


async def show(
        request: Request, 
        conn: Annotated[sqlite3.Connection, Depends(get_db)],
        category_id: int
        ):
    current_user = request.state.user
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    try:
        category_row = conn.execute(
            "SELECT * FROM category WHERE category_id = :category_id;", 
            {"category_id": category_id}
            ).fetchone()
    except Exception as e:
        logger.error(f"DB error getting category {category_id}: {e}", exc_info=True)

    return templates.TemplateResponse(
            request=request,
            name="hv/categories/show.xml",
            context={
                "category": category_row
                }
        )
    
async def edit(
        request: Request,
        current_user: Annotated[any, Depends(is_user)],
        conn: Annotated[sqlite3.Connection, Depends(get_db)], 
        category_id: int
        ):
    current_user = request.state.user
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    try:
        category_row = conn.execute(
            "SELECT * FROM category WHERE category_id = :category_id;", 
            {"category_id": category_id}
            ).fetchone()
    except Exception as e:
        logger.error(f"DB error getting category {category_id}: {e}", exc_info=True)
    
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/edit.xml",
        context={
            "category": category_row
        }
    )