from fastapi import APIRouter, Depends

from app.auth import auth_service
from app.controllers import public

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/v2",  public.home,   []),   # None

]

for method, path, handler, _ in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
    )


