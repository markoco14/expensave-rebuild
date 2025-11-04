from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")


async def home(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/app.html",
        context={}
    )

