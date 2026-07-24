from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin import IsAdmin
from app.keyboards.admin import choose_items_kb, entities_kb, subject_detail_kb
from app.keyboards.common import cancel_admin_kb
from app.models import BranchSubject, Subject
from app.services.admin_service import (
    create_subject,
    delete_subject,
    list_branches,
    list_subjects,
    rename_subject,
    toggle_branch_subject,
    toggle_subject,
)
from app.states.admin import SubjectForm
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_subjects")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _show_list(
    callback: CallbackQuery, session: AsyncSession, page: int = 0
) -> None:
    subjects = await list_subjects(session)
    await edit_or_send(
        callback,
        "📚 <b>Fanlar</b>\n\nFanni tanlab filial biriktirishini boshqaring.",
        entities_kb(subjects, "asu:view", "asu:add", "asu:page", page),
    )


@router.callback_query(F.data == "adm:subjects")
async def subjects_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_list(callback, session)
    await answer_callback(callback)


@router.callback_query(F.data.startswith("asu:page:"))
async def subjects_page(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_list(callback, session, int(callback.data.split(":")[2]))
    await answer_callback(callback)


@router.callback_query(F.data == "asu:add")
async def subject_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SubjectForm.name)
    await edit_or_send(callback, "➕ Yangi fan nomini yuboring:", cancel_admin_kb())
    await answer_callback(callback)


@router.message(SubjectForm.name)
async def subject_add_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    try:
        subject = await create_subject(session, message.text or "")
    except ValueError as exc:
        await message.answer(
            f"❌ {escape(str(exc))}\nBoshqa nom yuboring:",
            reply_markup=cancel_admin_kb(),
        )
        return
    await state.clear()
    await message.answer(f"✅ {escape(subject.name)} fani qo‘shildi.")


async def _show_subject(
    callback: CallbackQuery, session: AsyncSession, subject_id: int
) -> None:
    subject = await session.get(Subject, subject_id)
    if subject is None:
        await answer_callback(callback, "Fan topilmadi", True)
        return
    text = f"📚 <b>{escape(subject.name)}</b>\nHolati: {'✅ Faol' if subject.is_active else '⛔ Faol emas'}"
    await edit_or_send(callback, text, subject_detail_kb(subject.id, subject.is_active))
    await answer_callback(callback)


@router.callback_query(F.data.startswith("asu:view:"))
async def subject_view(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_subject(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("asu:rename:"))
async def subject_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(subject_id=int(callback.data.split(":")[2]))
    await state.set_state(SubjectForm.rename)
    await edit_or_send(callback, "✏️ Fanning yangi nomini yuboring:", cancel_admin_kb())
    await answer_callback(callback)


@router.message(SubjectForm.rename)
async def subject_rename_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    subject = await session.get(Subject, data["subject_id"])
    if subject is None:
        await state.clear()
        await message.answer("❌ Fan topilmadi")
        return
    try:
        await rename_subject(session, subject, message.text or "")
    except ValueError as exc:
        await message.answer(
            f"❌ {escape(str(exc))}\nBoshqa nom yuboring:",
            reply_markup=cancel_admin_kb(),
        )
        return
    await state.clear()
    await message.answer("✅ Fan nomi yangilandi.")


@router.callback_query(F.data.startswith("asu:toggle:"))
async def subject_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    subject = await session.get(Subject, int(callback.data.split(":")[2]))
    if subject:
        await toggle_subject(session, subject)
        await _show_subject(callback, session, subject.id)
        return
    await answer_callback(callback, "Fan topilmadi", True)


@router.callback_query(F.data.startswith("asu:delete:"))
async def subject_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    subject = await session.get(Subject, int(callback.data.split(":")[2]))
    if subject is None:
        await answer_callback(callback, "Fan topilmadi", True)
        return
    try:
        await delete_subject(session, subject)
    except ValueError as exc:
        await answer_callback(callback, str(exc), True)
        return
    await _show_list(callback, session)
    await answer_callback(callback, "Fan o‘chirildi")


async def _show_attach(
    callback: CallbackQuery, session: AsyncSession, subject_id: int
) -> None:
    subject = await session.get(Subject, subject_id)
    if subject is None:
        await answer_callback(callback, "Fan topilmadi", True)
        return
    branches = await list_branches(session)
    selected = set(
        (
            await session.scalars(
                select(BranchSubject.branch_id).where(
                    BranchSubject.subject_id == subject_id,
                    BranchSubject.is_active.is_(True),
                )
            )
        ).all()
    )
    await edit_or_send(
        callback,
        f"🏫 <b>{escape(subject.name)}</b> fanini filiallarda yoqing/o‘chiring:",
        choose_items_kb(
            branches, f"asua:{subject_id}", f"asu:view:{subject_id}", selected
        ),
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("asu:attach:"))
async def subject_attach(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_attach(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("asua:"))
async def subject_attach_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    _, subject_raw, branch_raw = callback.data.split(":")
    await toggle_branch_subject(session, int(branch_raw), int(subject_raw))
    await _show_attach(callback, session, int(subject_raw))
