from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import CATEGORY_LABELS
from app.filters.admin import IsAdmin
from app.services.competition_service import get_main_competition
from app.services.statistics_service import (
    admin_overview,
    breakdown_counts,
    time_series,
)
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_statistics")
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "adm:stats")
async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_main_competition(session)
    overview = await admin_overview(session, competition)
    top_text = "Hozircha ovoz yo‘q"
    if overview["top"]:
        student, votes = overview["top"]
        top_text = f"{escape(student.full_name)} — {votes} ovoz"
    text = (
        "📊 <b>ADMIN STATISTIKASI</b>\n\n"
        f"🗳 Jami ovozlar: {overview['total_votes']}\n"
        f"📅 Bugungi ovozlar: {overview['today_votes']}\n"
        f"👥 Jami foydalanuvchilar: {overview['total_users']}\n"
        f"✅ Ovoz berganlar: {overview['voted_users']}\n"
        f"▫️ Ovoz bermaganlar: {overview['not_voted_users']}\n"
        f"🏆 Eng ko‘p ovoz: {top_text}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏫 Filiallar", callback_data="adms:branch"),
                InlineKeyboardButton(text="📚 Fanlar", callback_data="adms:subject"),
            ],
            [InlineKeyboardButton(text="🎓 Toifalar", callback_data="adms:category")],
            [
                InlineKeyboardButton(text="📅 Kunlik", callback_data="adms:daily"),
                InlineKeyboardButton(text="🕐 Soatlik", callback_data="adms:hourly"),
            ],
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm:stats")],
            [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:home")],
        ]
    )
    await edit_or_send(callback, text, keyboard)
    await answer_callback(callback)


@router.callback_query(F.data.in_({"adms:branch", "adms:subject", "adms:category"}))
async def admin_breakdown(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_main_competition(session)
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    dimension = callback.data.split(":")[1]
    rows = await breakdown_counts(session, competition.id, dimension)
    labels = {"branch": "Filiallar", "subject": "Fanlar", "category": "Sinf toifalari"}
    lines = [f"📊 <b>{labels[dimension]} kesimida</b>", ""]
    for name, count in rows:
        shown_name = CATEGORY_LABELS.get(name, name)
        lines.append(f"• {escape(str(shown_name))}: {count} ta")
    if not rows:
        lines.append("Ma’lumot yo‘q.")
    await edit_or_send(
        callback,
        "\n".join(lines),
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:stats")]
            ]
        ),
    )
    await answer_callback(callback)


@router.callback_query(F.data.in_({"adms:daily", "adms:hourly"}))
async def admin_time_series(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_main_competition(session)
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    hourly = callback.data.endswith("hourly")
    rows = await time_series(session, competition.id, hours=hourly)
    lines = [f"📈 <b>{'Soatlik' if hourly else 'Kunlik'} ovozlar</b>", ""]
    for bucket, count in rows:
        fmt = "%d.%m %H:00" if hourly else "%d.%m.%Y"
        lines.append(f"• {bucket.strftime(fmt)} — {count} ta")
    if not rows:
        lines.append("Ma’lumot yo‘q.")
    await edit_or_send(
        callback,
        "\n".join(lines),
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:stats")]
            ]
        ),
    )
    await answer_callback(callback)
