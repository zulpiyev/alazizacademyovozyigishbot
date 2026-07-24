from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import CATEGORY_LABELS, CATEGORY_PRIMARY, CATEGORY_SECONDARY
from app.filters.admin import IsAdmin
from app.keyboards.admin import (
    choose_items_kb,
    competition_detail_kb,
    competition_list_kb,
)
from app.keyboards.common import cancel_admin_kb
from app.models import CompetitionBranch, CompetitionCategory, CompetitionSubject
from app.services.admin_service import list_branches, list_subjects
from app.services.competition_service import (
    create_competition,
    delete_competition,
    finish_competition,
    get_competition,
    list_competitions,
    pause_competition,
    resume_competition,
    set_main_and_start,
    toggle_competition_branch,
    toggle_competition_category,
    toggle_competition_subject,
)
from app.states.admin import CompetitionAdd
from app.utils.messages import answer_callback, edit_or_send
from app.utils.time import (
    competition_status,
    format_local,
    parse_local_datetime,
    remaining_text,
    status_label,
)

router = Router(name="admin_competitions")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _show_competitions(callback: CallbackQuery, session: AsyncSession) -> None:
    competitions = await list_competitions(session)
    await edit_or_send(
        callback,
        "🗳 <b>Tanlovlar</b>\n\n⭐ — asosiy tanlov",
        competition_list_kb(competitions),
    )
    await answer_callback(callback)


@router.callback_query(F.data == "adm:competitions")
async def competitions_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_competitions(callback, session)


@router.callback_query(F.data == "acp:add")
async def competition_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CompetitionAdd.name)
    await edit_or_send(callback, "➕ Tanlov nomini yuboring:", cancel_admin_kb())
    await answer_callback(callback)


@router.message(CompetitionAdd.name)
async def competition_add_name(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ Tanlov nomini to‘g‘ri yuboring:")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(CompetitionAdd.description)
    await message.answer(
        "Tanlov tavsifini yuboring. Tavsif bo‘lmasa /skip yozing:",
        reply_markup=cancel_admin_kb(),
    )


@router.message(CompetitionAdd.description)
async def competition_add_description(message: Message, state: FSMContext) -> None:
    description = (
        None
        if (message.text or "").strip().casefold() == "/skip"
        else (message.text or "").strip()
    )
    await state.update_data(description=description)
    await state.set_state(CompetitionAdd.starts_at)
    await message.answer(
        "🕐 Boshlanish sanasi va vaqtini yuboring.\nFormat: <code>25.07.2026 09:00</code>",
        reply_markup=cancel_admin_kb(),
    )


@router.message(CompetitionAdd.starts_at)
async def competition_add_start_time(message: Message, state: FSMContext) -> None:
    try:
        starts_at = parse_local_datetime(message.text or "")
    except ValueError:
        await message.answer(
            "❌ Format noto‘g‘ri. Masalan: <code>25.07.2026 09:00</code>"
        )
        return
    await state.update_data(starts_at=starts_at.isoformat())
    await state.set_state(CompetitionAdd.duration)
    await message.answer(
        "📅 Davomiylikni kunlarda yuboring. Standart: <code>7</code>",
        reply_markup=cancel_admin_kb(),
    )


@router.message(CompetitionAdd.duration)
async def competition_add_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    from datetime import datetime

    try:
        duration = int(message.text or "")
        if not 1 <= duration <= 365:
            raise ValueError
    except ValueError:
        await message.answer("❌ Davomiylik 1 dan 365 kungacha bo‘lsin:")
        return
    data = await state.get_data()
    starts_at = datetime.fromisoformat(data["starts_at"])
    competition = await create_competition(
        session,
        data["name"],
        data.get("description"),
        starts_at,
        duration,
    )
    await state.clear()
    await message.answer(
        f"✅ <b>{escape(competition.name)}</b> yaratildi.\n"
        "Barcha faol filial, fan va ikkala sinf toifasi biriktirildi. Kerak bo‘lsa tanlov ichidan o‘zgartiring.",
        reply_markup=competition_list_kb(await list_competitions(session)),
    )


async def _show_competition(
    callback: CallbackQuery, session: AsyncSession, comp_id: int
) -> None:
    competition = await get_competition(session, comp_id)
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    status = competition_status(
        competition.state, competition.starts_at, competition.ends_at
    )
    text = (
        f"🗳 <b>{escape(competition.name)}</b>\n\n"
        f"{escape(competition.description or 'Tavsif kiritilmagan')}\n\n"
        f"🕐 Boshlanish: {format_local(competition.starts_at)}\n"
        f"🏁 Tugash: {format_local(competition.ends_at)}\n"
        f"📅 Davomiylik: {competition.duration_days} kun\n"
        f"📌 Holat: {status_label(status)}\n"
        f"⭐ Asosiy: {'Ha' if competition.is_main else 'Yo‘q'}"
    )
    if status == "active":
        text += f"\n⏳ Qolgan vaqt: {remaining_text(competition.ends_at)}"
    await edit_or_send(callback, text, competition_detail_kb(competition))
    await answer_callback(callback)


@router.callback_query(F.data.startswith("acp:view:"))
async def competition_view(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_competition(callback, session, int(callback.data.split(":")[2]))


async def _refresh_comp(
    callback: CallbackQuery, session: AsyncSession, comp_id: int, notice: str
) -> None:
    await _show_competition(callback, session, comp_id)


@router.callback_query(F.data.startswith("acp:start:"))
async def competition_start(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_competition(session, int(callback.data.split(":")[2]))
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    await set_main_and_start(session, competition)
    await _refresh_comp(callback, session, competition.id, "Tanlov boshlandi")


@router.callback_query(F.data.startswith("acp:pause:"))
async def competition_pause(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_competition(session, int(callback.data.split(":")[2]))
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    try:
        await pause_competition(session, competition)
    except ValueError as exc:
        await answer_callback(callback, str(exc), True)
        return
    await _refresh_comp(callback, session, competition.id, "Tanlov to‘xtatildi")


@router.callback_query(F.data.startswith("acp:resume:"))
async def competition_resume(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_competition(session, int(callback.data.split(":")[2]))
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    try:
        await resume_competition(session, competition)
    except ValueError as exc:
        await answer_callback(callback, str(exc), True)
        return
    await _refresh_comp(callback, session, competition.id, "Tanlov davom ettirildi")


@router.callback_query(F.data.startswith("acp:finish:"))
async def competition_finish(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_competition(session, int(callback.data.split(":")[2]))
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    await finish_competition(session, competition)
    await _refresh_comp(callback, session, competition.id, "Tanlov yakunlandi")


@router.callback_query(F.data.startswith("acp:delete:"))
async def competition_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_competition(session, int(callback.data.split(":")[2]))
    if competition is None:
        await answer_callback(callback, "Tanlov topilmadi", True)
        return
    await delete_competition(session, competition)
    await _show_competitions(callback, session)


async def _show_comp_branches(
    callback: CallbackQuery, session: AsyncSession, comp_id: int
) -> None:
    branches = await list_branches(session)
    selected = set(
        (
            await session.scalars(
                select(CompetitionBranch.branch_id).where(
                    CompetitionBranch.competition_id == comp_id
                )
            )
        ).all()
    )
    await edit_or_send(
        callback,
        "🏫 Tanlov filiallarini yoqing/o‘chiring:",
        choose_items_kb(branches, f"acptb:{comp_id}", f"acp:view:{comp_id}", selected),
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("acp:branches:"))
async def competition_branches(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_comp_branches(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("acptb:"))
async def competition_branch_toggle(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    _, comp_raw, branch_raw = callback.data.split(":")
    await toggle_competition_branch(session, int(comp_raw), int(branch_raw))
    await _show_comp_branches(callback, session, int(comp_raw))


async def _show_comp_subjects(
    callback: CallbackQuery, session: AsyncSession, comp_id: int
) -> None:
    subjects = await list_subjects(session)
    selected = set(
        (
            await session.scalars(
                select(CompetitionSubject.subject_id).where(
                    CompetitionSubject.competition_id == comp_id
                )
            )
        ).all()
    )
    await edit_or_send(
        callback,
        "📚 Tanlov fanlarini yoqing/o‘chiring:",
        choose_items_kb(subjects, f"acpts:{comp_id}", f"acp:view:{comp_id}", selected),
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("acp:subjects:"))
async def competition_subjects(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_comp_subjects(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("acpts:"))
async def competition_subject_toggle(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    _, comp_raw, subject_raw = callback.data.split(":")
    await toggle_competition_subject(session, int(comp_raw), int(subject_raw))
    await _show_comp_subjects(callback, session, int(comp_raw))


async def _show_comp_categories(
    callback: CallbackQuery, session: AsyncSession, comp_id: int
) -> None:
    selected = set(
        (
            await session.scalars(
                select(CompetitionCategory.category).where(
                    CompetitionCategory.competition_id == comp_id
                )
            )
        ).all()
    )
    rows = []
    for category in (CATEGORY_PRIMARY, CATEGORY_SECONDARY):
        mark = "✅" if category in selected else "▫️"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {CATEGORY_LABELS[category]}",
                    callback_data=f"acptc:{comp_id}:{category}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"acp:view:{comp_id}")]
    )
    await edit_or_send(
        callback,
        "🎓 Tanlov sinf toifalarini yoqing/o‘chiring:",
        InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("acp:categories:"))
async def competition_categories(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    await _show_comp_categories(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("acptc:"))
async def competition_category_toggle(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    _, comp_raw, category = callback.data.split(":")
    await toggle_competition_category(session, int(comp_raw), category)
    await _show_comp_categories(callback, session, int(comp_raw))
