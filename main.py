""" Main application file """
from typing import Annotated
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/")
def get_index_page(request: Request):
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

@app.post("/signup", response_class=Response)
def signup(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    # db: Annotated[Session, Depends(get_db)],
    ):
    """Sign up a user"""
    response = Response(status_code=200)
    # response.set_cookie(
    #     key="session-id",
    #     value=session_cookie,
    #     httponly=True,
    #     secure=True,
    #     samesite="Lax"
    # )
    response.headers["HX-Redirect"] = "/"

    return response

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