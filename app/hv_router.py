from fastapi import APIRouter, Depends

from app.controllers.hv import application


hv_router = APIRouter()

# ('HTTP method', 'URI path', 'handler function', 'dependencies')
routes = [
    ("GET",     "/hv/index", application.index, []),
    ("GET",     "/hv/today", application.today, []),
    ("POST",    "/hv/today", application.store, []),
    ("GET",     "/hv/today/new",  application.new, []),

]

for method, path, handler, dependencies in routes:
    hv_router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=dependencies
    )


