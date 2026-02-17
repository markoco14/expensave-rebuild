from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def get(
        request: Request, 
        top_up_id: int
        ):
    return templates.TemplateResponse(
        request=request,
        name="hv/top-up/show.xml",
        context={}
    )