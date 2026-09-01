from fastapi import APIRouter, Depends

from src.controllers.web import user
from src.controllers.web import application, auth, bucket, public, purchase, top_up
from src.dependencies import is_purchase_owner, is_top_up_owner, is_user
from src.vendor.express_router import FastExpressRouter

router = FastExpressRouter()

# method | path | endpoint | permission
router.get(     "/",                               public.home,               Depends(is_user))
router.get(     "/signup",                         public.signup,             Depends(is_user))
router.get(     "/login",                          public.login,              Depends(is_user))
router.post(    "/register",                       auth.register,             Depends(is_user))
router.post(    "/session",                        auth.session,              Depends(is_user))
router.get(     "/logout",                         auth.logout,               Depends(is_user))
router.get(     "/today",                          application.today,         Depends(is_user))
router.post(    "/today",                          application.store,         Depends(is_user))
router.get(     "/purchases",                      purchase.list,             Depends(is_user))
router.post(    "/purchases",                      purchase.create,           Depends(is_user))
router.get(     "/purchases/new",                  purchase.new,              Depends(is_user))
router.get(     "/purchases/{purchase_id}",        purchase.show,             Depends(is_purchase_owner))
router.get(     "/purchases/{purchase_id}/edit",   purchase.edit,             Depends(is_purchase_owner))
router.put(     "/purchases/{purchase_id}",        purchase.update,           Depends(is_purchase_owner))
router.delete(  "/purchases/{purchase_id}",        purchase.delete,           Depends(is_purchase_owner))
router.get(     "/me",                             user.me,                   Depends(is_user))
router.post(    "/buckets",                        bucket.create,             Depends(is_user))
router.post(    "/buckets/daily",                  bucket.create,             Depends(is_user))
router.delete(  "/buckets/{bucket_id}",            bucket.delete,             Depends(is_user))
router.post(    "/buckets/{bucket_id}/top-up",     top_up.store,              Depends(is_user))
router.delete(  "/top-up/{top_up_id}",             top_up.delete,             Depends(is_top_up_owner))
router.delete(  "/toast/delete",                   application.delete_toast,  None)


