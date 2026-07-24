from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)
router = Router(name="errors")


@router.error()
async def global_error_handler(event: ErrorEvent) -> bool:
    exception = event.exception
    logger.error(
        "Unhandled bot error",
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    update = event.update
    try:
        if update.callback_query:
            await update.callback_query.answer(
                "❌ Xatolik yuz berdi. Qayta urinib ko‘ring.", show_alert=True
            )
        elif update.message:
            await update.message.answer(
                "❌ Xatolik yuz berdi. /start orqali qayta urinib ko‘ring."
            )
    except Exception:
        logger.debug("Could not send error notification to user", exc_info=True)
    return True
