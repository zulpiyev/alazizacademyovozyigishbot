from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import get_settings
from app.database.seed import seed_defaults
from app.database.session import SessionFactory, engine, initialize_database
from app.handlers import setup_root_router
from app.middlewares.database import DbSessionMiddleware
from app.services.scheduler_service import create_scheduler, scheduler_tick
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    settings = get_settings()
    await initialize_database()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(DbSessionMiddleware(SessionFactory))
    dispatcher.include_router(setup_root_router())

    async with SessionFactory() as session:
        await seed_defaults(session, settings)

    scheduler = create_scheduler(
        bot, SessionFactory, settings.scheduler_interval_seconds
    )
    scheduler.start()
    await scheduler_tick(bot, SessionFactory)

    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Bosh menyu"),
                BotCommand(command="admin", description="Admin panel"),
                BotCommand(command="result", description="1–2–3-o‘rinlar Excel"),
            ]
        )
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Al-Aziz Voting Bot ishga tushdi")
        await dispatcher.start_polling(
            bot, allowed_updates=dispatcher.resolve_used_update_types()
        )
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
