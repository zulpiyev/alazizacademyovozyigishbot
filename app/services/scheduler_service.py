from __future__ import annotations

import logging
from html import escape

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Competition
from app.services.broadcast_service import broadcast_text
from app.utils.time import competition_status, ensure_utc, format_local, utc_now

logger = logging.getLogger(__name__)


async def _send_and_mark(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    competition_id: int,
    field_name: str,
    text: str,
) -> None:
    await broadcast_text(bot, session_factory, text)
    async with session_factory() as session:
        competition = await session.get(Competition, competition_id)
        if competition:
            setattr(competition, field_name, True)
            await session.commit()


async def scheduler_tick(
    bot: Bot, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    now = utc_now()
    pending: list[tuple[int, str, str]] = []
    async with session_factory() as session:
        competitions = list(
            (
                await session.scalars(
                    select(Competition)
                    .where(Competition.is_main.is_(True))
                    .with_for_update(skip_locked=True)
                )
            ).all()
        )
        for competition in competitions:
            status = competition_status(
                competition.state, competition.starts_at, competition.ends_at, now
            )
            if status == "active" and competition.state == "scheduled":
                competition.state = "active"
            if status == "finished" and competition.state != "finished":
                competition.state = "finished"

            remaining_seconds = max(
                0, int((ensure_utc(competition.ends_at) - now).total_seconds())
            )
            if status == "active" and not competition.notify_start_sent:
                pending.append(
                    (
                        competition.id,
                        "notify_start_sent",
                        f"🏆 <b>{escape(competition.name)}</b> boshlandi!\n\n"
                        f"Ovoz berish yakuni: {format_local(competition.ends_at)}\n"
                        "Eng yaxshi o‘quvchiga ovoz bering.",
                    )
                )
            if (
                status == "active"
                and remaining_seconds <= 3 * 86400
                and not competition.notify_3d_sent
            ):
                pending.append(
                    (
                        competition.id,
                        "notify_3d_sent",
                        f"⏳ {escape(competition.name)} tugashiga 3 kun qoldi.",
                    )
                )
            if (
                status == "active"
                and remaining_seconds <= 86400
                and not competition.notify_1d_sent
            ):
                pending.append(
                    (
                        competition.id,
                        "notify_1d_sent",
                        f"⏳ {escape(competition.name)} tugashiga 1 kun qoldi.",
                    )
                )
            if (
                status == "active"
                and remaining_seconds <= 3600
                and not competition.notify_1h_sent
            ):
                pending.append(
                    (
                        competition.id,
                        "notify_1h_sent",
                        f"⏳ {escape(competition.name)} tugashiga 1 soat qoldi.",
                    )
                )
            if status == "finished" and not competition.notify_end_sent:
                pending.append(
                    (
                        competition.id,
                        "notify_end_sent",
                        f"🔴 <b>{escape(competition.name)}</b> yakunlandi!\n\nYakuniy natijalarni botdagi statistika bo‘limida ko‘ring.",
                    )
                )
        await session.commit()

    for competition_id, field_name, text in pending:
        try:
            await _send_and_mark(bot, session_factory, competition_id, field_name, text)
        except Exception:
            logger.exception(
                "Automatic notification failed: competition=%s field=%s",
                competition_id,
                field_name,
            )


def create_scheduler(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    interval_seconds: int,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(
        scheduler_tick,
        "interval",
        seconds=max(30, interval_seconds),
        kwargs={"bot": bot, "session_factory": session_factory},
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
    )
    return scheduler
