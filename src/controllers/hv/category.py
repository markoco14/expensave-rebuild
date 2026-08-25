from datetime import datetime, timezone
import sqlite3
from typing import Annotated
from zoneinfo import ZoneInfo
from fastapi import Depends, Request, Response
from fastapi.templating import Jinja2Templates

from src.respository.category import list_with_top_ups
from src.config import get_db, templates
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


async def new(
        request: Request, 
        current_user: Annotated[any, Depends(is_user)]
        ):
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/new.xml",
        context={}
    )


async def store(
        request: Request, 
        current_user: Annotated[any, Depends(is_user)],
        conn: Annotated[sqlite3.Connection, Depends(get_db)]
        ):
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    form_data = await request.form()
    form_name = form_data.get("name", "").strip()
    form_is_daily = form_data.get("is_daily", "").strip()

    if not form_name or not form_is_daily:
        return Response(status_code=422, content="form data missing")

    if form_is_daily not in ("0", "1"):
        return Response(status_code=422, content="invalid tracking value")

    try:
        conn.execute(
            "INSERT INTO category (name, is_daily, user_id) VALUES (:name, :is_daily, :user_id);", 
            {"name": form_name, "is_daily": form_is_daily, "user_id": current_user.user_id}
            )
        conn.commit()
    except Exception as e:
        logger.error(f"DB error storing category: {e}", exc_info=True)
        return Response(status_code=500, content="server error, sorry")
    
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/_form-fields.xml",
        context={"saved": True}
    )


async def show(
        request: Request, 
        current_user: Annotated[any, Depends(is_user)],
        conn: Annotated[sqlite3.Connection, Depends(get_db)],
        category_id: int
        ):

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

async def update(
        request: Request,
        current_user: Annotated[any, Depends(is_user)],
        conn: Annotated[sqlite3.Connection, Depends(get_db)], 
        category_id: int
        ):
    if not current_user:
        return Response(status_code=401, content="not authenticated")

    form_data = await request.form()
    name = form_data.get("name", "").strip()
    is_daily = form_data.get("is_daily", "").strip()

    if not name:
        print("no name")

    if not is_daily:
        print("no is daily")

    if not name or not is_daily:
        return Response(status_code=422, content="incomplete form")

    if is_daily not in ("0", "1"):
        print("is daily not 0 or 1")
        return Response(status_code=422, content="invalid is daily")

    try:
        conn.execute(
            "UPDATE category SET name = :name, is_daily = :is_daily WHERE category_id = :category_id;", 
            {
                "name": name,
                "is_daily": is_daily,
                "category_id": category_id
            }
            )
        conn.commit()
    except Exception as e:
        logger.error(f"DB error updating category {category_id}: {e}", exc_info=True)
        return Response(status_code=500, content="something went wrong on our end")

    try:
        category_row = conn.execute(
            "SELECT * FROM category WHERE category_id = :category_id;", 
            {"category_id": category_id}
            ).fetchone()
    except Exception as e:
        logger.error(f"DB error getting category {category_id}: {e}", exc_info=True)
    
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/_form-fields.xml",
        context={
            "saved": True,
            "category": category_row
        }
    )


async def delete(
        request: Request,
        current_user: Annotated[any, Depends(is_user)],
        conn: Annotated[sqlite3.Connection, Depends(get_db)], 
        category_id: int
        ):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"
    if not current_user:
        return Response(status_code=401, content="not authenticated")

    try:
        conn.execute("DELETE FROM category WHERE category_id = :category_id;", {"category_id": category_id})
        conn.commit()
    except Exception as e:
        logger.error(f"DB error deleting category: {e}", exc_info=True)
        return Response(status_code=500, content="something went wrong")
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/_deleted.xml",
        context={},
        headers={"Content-Type": content_type}
    )
    return Response(status_code=200, content="success")

    