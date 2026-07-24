from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import CATEGORY_LABELS
from app.keyboards.user import categories_kb, stats_results_kb, subjects_kb
from app.services.competition_service import get_main_competition, participating_subjects
from app.services.statistics_service import group_results
from app.utils.competition_text import step_text
from app.utils.messages import answer_callback, edit_or_send
from app.utils.time import competition_status, remaining_text

router = Router(name="user_statistics")


@router.callback_query(F.data == "main:stats")
async def stats_start(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_main_competition(session)
    if competition is None:
        await answer_callback(callback, "Hozircha tanlov mavjud emas", True)
        return
    subjects = await participating_subjects(session, competition.id)
    await edit_or_send(
        callback,
        step_text("📊 <b>Statistika uchun fanni tanlang</b>", competition),
        subjects_kb(subjects, "ssub", "main:home"),
    )
    await answer_callback(callback)


async def _show_stats_categories(
    callback: CallbackQuery, session: AsyncSession, subject_id: int
) -> None:
    competition = await get_main_competition(session)
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    keyboard = categories_kb(subject_id, "sshow", "main:stats")
    await edit_or_send(
        callback, step_text("🎓 <b>Sinfni tanlang</b>", competition), keyboard
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("ssub:"))
async def stats_subject(callback: CallbackQuery, session: AsyncSession) -> None:
    _, subject_raw = callback.data.split(":")
    await _show_stats_categories(callback, session, int(subject_raw))


@router.callback_query(F.data.startswith("scat:"))
async def stats_category_back(callback: CallbackQuery, session: AsyncSession) -> None:
    _, subject_raw = callback.data.split(":")
    await _show_stats_categories(callback, session, int(subject_raw))


@router.callback_query(F.data.startswith("sshow:"))
async def stats_show(callback: CallbackQuery, session: AsyncSession) -> None:
    _, subject_raw, category, page_raw = callback.data.split(":")
    subject_id, page = int(subject_raw), int(page_raw)
    competition = await get_main_competition(session)
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    results, total = await group_results(
        session, competition.id, None, subject_id, category
    )
    subject_name = results[0].student.subject.name if results else "Tanlangan fan"
    title = (
        "YAKUNIY NATIJALAR"
        if competition_status(
            competition.state, competition.starts_at, competition.ends_at
        )
        == "finished"
        else "JORIY NATIJALAR"
    )
    lines = [
        f"🏆 <b>{title}</b>",
        "",
        "🏫 Filiallararo musobaqa",
        f"📚 Fan: {escape(subject_name)}",
        f"🎓 Toifa: {CATEGORY_LABELS[category]}",
        "",
    ]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    if not results:
        lines.append("Bu bo‘limda o‘quvchilar mavjud emas.")
    page_size = 10
    total_pages = max(1, (len(results) + page_size - 1) // page_size)
    page = min(max(page, 0), total_pages - 1)
    page_results = results[page * page_size : (page + 1) * page_size]
    for item in page_results:
        medal = medals.get(item.rank, "▫️")
        lines.append(
            f"{medal} {item.rank}. {escape(item.student.full_name)} — "
            f"{escape(item.student.branch.name)} — {item.votes} ovoz — "
            f"{item.percent:.1f}%"
        )
    lines.extend(["", f"👥 Jami ovozlar: {total} ta"])
    status = competition_status(
        competition.state, competition.starts_at, competition.ends_at
    )
    if status == "active":
        lines.append(f"⏳ Qolgan vaqt: {remaining_text(competition.ends_at)}")
    await edit_or_send(
        callback,
        "\n".join(lines),
        stats_results_kb(subject_id, category, page, len(results), page_size),
    )
    await answer_callback(callback)
