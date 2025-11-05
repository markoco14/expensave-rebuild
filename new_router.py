from fastapi import APIRouter, Depends

from app.controllers import application, auth, bucket, budget, public, purchase, user
from app.dependencies import is_user

router = APIRouter()

# routes follow ('method', 'path', 'endpoint/handler', 'dependencies')
routes = [
    ("GET",     "/",                            public.home,        [Depends(is_user)]),   # None
    ("GET",     "/signup",                      public.signup,      [Depends(is_user)]),
    ("GET",     "/login",                       public.login,       [Depends(is_user)]),

    ("POST",    "/register",                    auth.register,      [Depends(is_user)]),
    ("POST",    "/session",                     auth.session,       [Depends(is_user)]),
    ("GET",     "/logout",                      auth.logout,        [Depends(is_user)]),

    ("GET",     "/app",                         application.home,   [Depends(is_user)]),
    
    ("GET",     "/purchases",                   purchase.list,      [Depends(is_user)]),
    ("POST",    "/purchases",                   purchase.create,    [Depends(is_user)]),
    ("GET",     "/purchases/new",               purchase.new,       [Depends(is_user)]),

    ("GET",     "/me",                          user.me,            [Depends(is_user)]),

    ("POST",    "/buckets",                     bucket.create,      [Depends(is_user)]),
    ("POST",    "/buckets/daily",               bucket.create,      [Depends(is_user)]),
    ("DELETE",  "/buckets/{bucket_id}",         bucket.delete,      [Depends(is_user)]),

    ("POST",    "/budgets",                     budget.create,      [Depends(is_user)]),

]

for method, path, handler, dependencies in routes:
    router.add_api_route(
        path=path,
        endpoint=handler,
        methods=[method],
        dependencies=dependencies
    )


