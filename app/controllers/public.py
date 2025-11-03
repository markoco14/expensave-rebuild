from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new/index.html",
        context={}
    )