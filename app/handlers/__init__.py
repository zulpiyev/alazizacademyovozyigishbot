from aiogram import Router

from app.handlers import errors
from app.handlers.admin import setup_admin_router
from app.handlers.user import setup_user_router


def setup_root_router() -> Router:
    router = Router(name="root")
    router.include_router(errors.router)
    router.include_router(setup_admin_router())
    router.include_router(setup_user_router())
    return router
