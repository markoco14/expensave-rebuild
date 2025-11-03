from fastapi import APIRouter, Depends

from app.controllers import public
from app.dependencies import is_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",         public.home,        [Depends(is_user)]),   # None
    ("GET",     "/signup",   public.signup,      [Depends(is_user)]),
    ("POST",    "/register", public.register,    [Depends(is_user)]),
    ("GET",     "/login",    public.login,       [Depends(is_user)]),
    ("POST",    "/session",  public.session,     [Depends(is_user)]),
    ("GET",     "/app",      public.app,         [Depends(is_user)]),

]

for method, path, handler, dependencies in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=dependencies
    )


