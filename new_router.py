from fastapi import APIRouter, Depends

from app.controllers import public
from app.dependencies import is_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/v2",          public.home,        [Depends(is_user)]),   # None
    ("GET",     "/v2/signup",   public.signup,      [Depends(is_user)]),
    ("POST",    "/v2/register", public.register,    [Depends(is_user)]),
    ("GET",     "/v2/login",    public.login,       [Depends(is_user)]),
    ("POST",    "/v2/session",  public.session,     [Depends(is_user)]),
    ("GET",     "/v2/app",      public.app,         [Depends(is_user)]),

]

for method, path, handler, dependencies in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=dependencies
    )


