from aiogram import Router

from app.handlers.admin import (
    branches,
    broadcasts,
    competitions,
    excel,
    panel,
    settings,
    statistics,
    students,
    subjects,
)


def setup_admin_router() -> Router:
    router = Router(name="admin")
    router.include_router(panel.router)
    router.include_router(branches.router)
    router.include_router(subjects.router)
    router.include_router(students.router)
    router.include_router(competitions.router)
    router.include_router(excel.router)
    router.include_router(broadcasts.router)
    router.include_router(statistics.router)
    router.include_router(settings.router)
    return router
