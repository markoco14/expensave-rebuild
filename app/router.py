from fastapi import APIRouter, Depends

from app.controllers import application, auth, bucket, public, purchase, user
from app.dependencies import is_purchase_owner, is_user

router = APIRouter()

# ('HTTP method', 'URI path', 'handler function', 'dependencies')
routes = [
    ("GET",     "/",                                public.home,        [Depends(is_user)]),   # None
    ("GET",     "/signup",                          public.signup,      [Depends(is_user)]),
    ("GET",     "/login",                           public.login,       [Depends(is_user)]),

    ("POST",    "/register",                        auth.register,      [Depends(is_user)]),
    ("POST",    "/session",                         auth.session,       [Depends(is_user)]),
    ("GET",     "/logout",                          auth.logout,        [Depends(is_user)]),

    ("GET",     "/today",                           application.today,  [Depends(is_user)]),
    ("GET",     "/stats",                           application.stats,  [Depends(is_user)]),
    
    ("GET",     "/purchases",                       purchase.list,      [Depends(is_user)]),
    ("POST",    "/purchases",                       purchase.create,    [Depends(is_user)]),
    ("GET",     "/purchases/new",                   purchase.new,       [Depends(is_user)]),
    ("GET",     "/purchases/{purchase_id}",         purchase.show,      [Depends(is_user), Depends(is_purchase_owner)]),
    ("GET",     "/purchases/{purchase_id}/edit",    purchase.edit,      [Depends(is_user), Depends(is_purchase_owner)]),
    ("PUT",     "/purchases/{purchase_id}",         purchase.update,    [Depends(is_user), Depends(is_purchase_owner)]),
    ("DELETE",  "/purchases/{purchase_id}",         purchase.delete,    [Depends(is_user), Depends(is_purchase_owner)]),

    ("GET",     "/me",                              user.me,            [Depends(is_user)]),

    ("POST",    "/buckets",                         bucket.create,      [Depends(is_user)]),
    ("POST",    "/buckets/daily",                   bucket.create,      [Depends(is_user)]),
    ("DELETE",  "/buckets/{bucket_id}",             bucket.delete,      [Depends(is_user)]),

    ("DELETE",  "/toast/delete",                    application.delete_toast,   [])
]

for method, path, handler, dependencies in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=dependencies
    )


