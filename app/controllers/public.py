from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")


def home(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/index.html",
        context={}
    )


def signup(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/signup.html",
        context={}
    )


async def login(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/login.html",
        context={}
    )
