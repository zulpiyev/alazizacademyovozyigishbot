from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Broadcast, User

logger = logging.getLogger(__name__)


async def broadcast_copy(
    bot: Bot,
    session: AsyncSession,
    source_message: Message,
    admin_telegram_id: int,
) -> tuple[int, int]:
    user_ids = list(
        (
            await session.scalars(
                select(User.telegram_id).where(User.is_blocked.is_(False))
            )
        ).all()
    )
    sent = 0
    failed = 0
    for telegram_id in user_ids:
        try:
            await source_message.copy_to(telegram_id)
            sent += 1
            await asyncio.sleep(0.04)
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 1)
            try:
                await source_message.copy_to(telegram_id)
                sent += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            failed += 1
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if user:
                user.is_blocked = True
        except Exception:
            failed += 1
            logger.exception("Broadcast failed for %s", telegram_id)
    message_type = "text"
    file_id = None
    if source_message.photo:
        message_type = "photo"
        file_id = source_message.photo[-1].file_id
    elif source_message.video:
        message_type = "video"
        file_id = source_message.video.file_id
    session.add(
        Broadcast(
            admin_telegram_id=admin_telegram_id,
            message_type=message_type,
            content=source_message.text or source_message.caption,
            telegram_file_id=file_id,
            sent_count=sent,
            failed_count=failed,
            status="completed",
        )
    )
    await session.commit()
    return sent, failed


async def broadcast_text(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    text: str,
) -> tuple[int, int]:
    async with session_factory() as session:
        user_ids = list(
            (
                await session.scalars(
                    select(User.telegram_id).where(User.is_blocked.is_(False))
                )
            ).all()
        )
        sent = 0
        failed = 0
        for telegram_id in user_ids:
            try:
                await bot.send_message(telegram_id, text)
                sent += 1
                await asyncio.sleep(0.04)
            except TelegramForbiddenError:
                failed += 1
                user = await session.scalar(
                    select(User).where(User.telegram_id == telegram_id)
                )
                if user:
                    user.is_blocked = True
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after + 1)
            except Exception:
                failed += 1
                logger.exception("Automatic broadcast failed for %s", telegram_id)
        await session.commit()
        return sent, failed
