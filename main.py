""" Main application file """
from typing import Annotated
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates

from app.auth import auth_service, auth_router

app = FastAPI()
app.include_router(auth_router.router)

templates = Jinja2Templates(directory="templates")


@app.get("/")
def get_index_page(request: Request):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
        )
    
    currency = "TWD"
    context={"currency": currency}
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.get("/signup")
def get_sign_up_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
    )
@app.get("/signin")
def get_sign_in_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signin.html",
    )

# @app.post("/signup", response_class=Response)
# def signup(
#     request: Request,
#     response: Response,
#     email: Annotated[str, Form()],
#     password: Annotated[str, Form()],
#     # db: Annotated[Session, Depends(get_db)],
#     ):
#     """Sign up a user"""
#     response = Response(status_code=200)
#     session_cookie = 'abc'
#     response.set_cookie(
#         key="session-id",
#         value=session_cookie,
#         httponly=True,
#         secure=True,
#         samesite="Lax"
#     )
#     response.headers["HX-Redirect"] = "/"

#     return response

@app.post("/track-purchase")
def track_purchase(
    request: Request,
    items: Annotated[str, Form()],
    price: Annotated[str, Form()],
    currency: Annotated[str, Form()],
    location: Annotated[str, Form()]
    ):
    currency = "TWD"
    context={"currency": currency}
    return templates.TemplateResponse(
        request=request,
        name="track-purchase-form.html",
        context=context
        )