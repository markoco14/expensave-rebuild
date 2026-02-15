from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")

async def list(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="hv/bucket/index.xml",
        context={}
    )
