from fastapi import APIRouter, Depends

from src.controllers.web import user
from src.controllers.web import application, auth, bucket, public, purchase, top_up
from src.dependencies import is_purchase_owner, is_top_up_owner, is_user

router = APIRouter()

router.add_api_route(methods=["GET"],       path="/",                               endpoint=public.home,               dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/signup",                         endpoint=public.signup,             dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/login",                          endpoint=public.login,              dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/register",                       endpoint=auth.register,             dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/session",                        endpoint=auth.session,              dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/logout",                         endpoint=auth.logout,               dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/today",                          endpoint=application.today,         dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/today",                          endpoint=application.store,         dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/purchases",                      endpoint=purchase.list,             dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/purchases",                      endpoint=purchase.create,           dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/purchases/new",                  endpoint=purchase.new,              dependencies=[Depends(is_user)])
router.add_api_route(methods=["GET"],       path="/purchases/{purchase_id}",        endpoint=purchase.show,             dependencies=[Depends(is_user), Depends(is_purchase_owner)])
router.add_api_route(methods=["GET"],       path="/purchases/{purchase_id}/edit",   endpoint=purchase.edit,             dependencies=[Depends(is_user), Depends(is_purchase_owner)])
router.add_api_route(methods=["PUT"],       path="/purchases/{purchase_id}",        endpoint=purchase.update,           dependencies=[Depends(is_user), Depends(is_purchase_owner)])
router.add_api_route(methods=["DELETE"],    path="/purchases/{purchase_id}",        endpoint=purchase.delete,           dependencies=[Depends(is_user), Depends(is_purchase_owner)])
router.add_api_route(methods=["GET"],       path="/me",                             endpoint=user.me,                   dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/buckets",                        endpoint=bucket.create,             dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/buckets/daily",                  endpoint=bucket.create,             dependencies=[Depends(is_user)])
router.add_api_route(methods=["DELETE"],    path="/buckets/{bucket_id}",            endpoint=bucket.delete,             dependencies=[Depends(is_user)])
router.add_api_route(methods=["POST"],      path="/buckets/{bucket_id}/top-up",     endpoint=top_up.store,              dependencies=[Depends(is_user)])
router.add_api_route(methods=["DELETE"],    path="/top-up/{top_up_id}",             endpoint=top_up.delete,             dependencies=[Depends(is_user), Depends(is_top_up_owner)])
router.add_api_route(methods=["DELETE"],    path="/toast/delete",                   endpoint=application.delete_toast,  dependencies=None)



# ('HTTP method', 'URI path', 'handler function', 'dependencies')
# routes = [
#     ("GET",     "/",                                public.home,        [Depends(is_user)]),   # None
#     ("GET",     "/signup",                          public.signup,      [Depends(is_user)]),
#     ("GET",     "/login",                           public.login,       [Depends(is_user)]),

#     ("POST",    "/register",                        auth.register,      [Depends(is_user)]),
#     ("POST",    "/session",                         auth.session,       [Depends(is_user)]),
#     ("GET",     "/logout",                          auth.logout,        [Depends(is_user)]),

#     ("GET",     "/today",                           application.today,  [Depends(is_user)]),
#     ("POST",    "/today",                           application.store,  [Depends(is_user)]),
#     # ("GET",     "/stats",                           application.stats,  [Depends(is_user)]),
    
#     ("GET",     "/purchases",                       purchase.list,      [Depends(is_user)]),
#     ("POST",    "/purchases",                       purchase.create,    [Depends(is_user)]),
#     ("GET",     "/purchases/new",                   purchase.new,       [Depends(is_user)]),
#     ("GET",     "/purchases/{purchase_id}",         purchase.show,      [Depends(is_user), Depends(is_purchase_owner)]),
#     ("GET",     "/purchases/{purchase_id}/edit",    purchase.edit,      [Depends(is_user), Depends(is_purchase_owner)]),
#     ("PUT",     "/purchases/{purchase_id}",         purchase.update,    [Depends(is_user), Depends(is_purchase_owner)]),
#     ("DELETE",  "/purchases/{purchase_id}",         purchase.delete,    [Depends(is_user), Depends(is_purchase_owner)]),

#     ("GET",     "/me",                              user.me,            [Depends(is_user)]),

#     ("POST",    "/buckets",                         bucket.create,      [Depends(is_user)]),
#     ("POST",    "/buckets/daily",                   bucket.create,      [Depends(is_user)]),
#     ("DELETE",  "/buckets/{bucket_id}",             bucket.delete,      [Depends(is_user)]),

#     ("POST",    "/buckets/{bucket_id}/top-up",      top_up.store,       [Depends(is_user)]),

#     ("DELETE",  "/top-up/{top_up_id}",              top_up.delete,      [Depends(is_user), Depends(is_top_up_owner)]),

#     ("DELETE",  "/toast/delete",                    application.delete_toast,   [])
# ]

# for method, path, handler, dependencies in routes:
#     router.add_api_route(
#         path=path,
#         endpoint=handler,
#         methods=[method],
#         dependencies=dependencies
#     )




