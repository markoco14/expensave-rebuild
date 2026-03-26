from fastapi import APIRouter, Depends

from app.controllers.hv import application, auth, bucket, purchase, top_up
from app.dependencies import is_user


hv_router = APIRouter()

# ('HTTP method', 'URI path', 'handler function', 'dependencies')
routes = [
    ("GET",     "/hv/index",        application.index,  [Depends(is_user)]),
    ("GET",     "/hv/today",        application.today,  [Depends(is_user)]),
    ("POST",    "/hv/today",        application.store,  [Depends(is_user)]),
    ("GET",     "/hv/today/new",    application.new,    [Depends(is_user)]),
    
    ("POST",    "/hv/login",        auth.login,  []),
    ("GET",    "/hv/logout",        auth.logout,  [Depends(is_user)]),

    ("GET",     "/hv/purchases/{purchase_id}",          purchase.show,      [Depends(is_user)]),
    ("GET",     "/hv/purchases/{purchase_id}/edit",     purchase.edit,      [Depends(is_user)]),
    ("POST",    "/hv/purchases/{purchase_id}/edit",     purchase.update,    [Depends(is_user)]),
    ("POST",    "/hv/purchases/{purchase_id}/delete",   purchase.delete,    [Depends(is_user)]),

    ("GET",     "/hv/buckets",  bucket.list, [Depends(is_user)]),
    ("GET",     "/hv/buckets/{bucket_id}", bucket.show, [Depends(is_user)]),

    ("GET",     "/hv/top-up/{top_up_id}/edit",  top_up.edit,    [Depends(is_user)]),
    ("POST",    "/hv/top-up/{top_up_id}/update",       top_up.update,  [Depends(is_user)])
]

for method, path, handler, dependencies in routes:
    hv_router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=dependencies
    )


