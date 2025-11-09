from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")


def home(request: Request):
    if request.state.user:
        return RedirectResponse(url="/today", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


def signup(request: Request):
    if request.state.user:
        return RedirectResponse(url="/today", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={}
    )


async def login(request: Request):
    if request.state.user:
        return RedirectResponse(url="/today", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )
