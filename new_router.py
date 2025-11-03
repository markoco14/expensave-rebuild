from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import public

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/v2",          public.home,        []),   # None
    ("GET",     "/v2/signup",   public.signup,      []),
    ("POST",    "/v2/register", public.register,    []),
    ("GET",     "/v2/login",    public.login,       []),
    ("POST",    "/v2/session",  public.session,     []),
    ("GET",     "/v2/app",      public.app,         []),

]

for method, path, handler, _ in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
    )


