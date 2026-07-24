from aiogram import Router

from app.handlers.user import start, statistics, voting


def setup_user_router() -> Router:
    router = Router(name="user")
    router.include_router(start.router)
    router.include_router(voting.router)
    router.include_router(statistics.router)
    return router
