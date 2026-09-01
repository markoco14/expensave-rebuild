from fastapi import Depends

from src.controllers.hv import application, auth, category, purchase, top_up
from src.dependencies import is_user
from src.vendor.express_router import ExpressRouter


hv_router = ExpressRouter()

hv_router.get(  "/hv/index",                            application.index,  Depends(is_user))
hv_router.get(  "/hv/today",                            application.today,  Depends(is_user))
hv_router.post( "/hv/today",                            application.store,  Depends(is_user))
hv_router.get(  "/hv/today/new",                        application.new,    Depends(is_user))

hv_router.post( "/hv/login",                            auth.login,         None)
hv_router.get(  "/hv/logout",                           auth.logout,        Depends(is_user))

hv_router.get(  "/hv/purchases/{purchase_id}",          purchase.show,      Depends(is_user)),
hv_router.get(  "/hv/purchases/{purchase_id}/edit",     purchase.edit,      Depends(is_user)),
hv_router.post( "/hv/purchases/{purchase_id}/edit",     purchase.update,    Depends(is_user)),
hv_router.post( "/hv/purchases/{purchase_id}/delete",   purchase.delete,    Depends(is_user)),

hv_router.get(  "/hv/categories",                       category.list,      Depends(is_user)),
hv_router.get(  "/hv/categories/new",                   category.new,       None),
hv_router.post( "/hv/categories",                       category.store,     None),
hv_router.get(  "/hv/categories/{category_id}",         category.show,      Depends(is_user)),
hv_router.get(  "/hv/categories/{category_id}/edit",    category.edit,      None),
hv_router.post( "/hv/categories/{category_id}/edit",    category.update,    None),
hv_router.post( "/hv/categories/{category_id}/delete",  category.delete,    None),

hv_router.get(  "/hv/top-up/{top_up_id}/edit",          top_up.edit,        Depends(is_user)),
hv_router.post( "/hv/top-up/{top_up_id}/update",        top_up.update,      Depends(is_user))
