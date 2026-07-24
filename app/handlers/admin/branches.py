from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin import IsAdmin
from app.keyboards.admin import branch_detail_kb, entities_kb
from app.keyboards.common import cancel_admin_kb
from app.models import Branch
from app.services.admin_service import (
    create_branch,
    delete_branch,
    list_branches,
    rename_branch,
    toggle_branch,
)
from app.states.admin import BranchForm
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_branches")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _show_list(
    callback: CallbackQuery, session: AsyncSession, page: int = 0
) -> None:
    branches = await list_branches(session)
    await edit_or_send(
        callback,
        "🏫 <b>Filiallar</b>\n\n✅ faol, ⛔ vaqtincha o‘chirilgan",
        entities_kb(branches, "abr:view", "abr:add", "abr:page", page),
    )


@router.callback_query(F.data == "adm:branches")
async def branches_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_list(callback, session)
    await answer_callback(callback)


@router.callback_query(F.data.startswith("abr:page:"))
async def branches_page(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_list(callback, session, int(callback.data.split(":")[2]))
    await answer_callback(callback)


@router.callback_query(F.data == "abr:add")
async def branch_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BranchForm.name)
    await edit_or_send(callback, "➕ Yangi filial nomini yuboring:", cancel_admin_kb())
    await answer_callback(callback)


@router.message(BranchForm.name)
async def branch_add_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    try:
        branch = await create_branch(session, message.text or "")
    except ValueError as exc:
        await message.answer(
            f"❌ {escape(str(exc))}\nBoshqa nom yuboring:",
            reply_markup=cancel_admin_kb(),
        )
        return
    await state.clear()
    await message.answer(
        f"✅ {escape(branch.name)} filiali qo‘shildi.",
        reply_markup=entities_kb(
            await list_branches(session), "abr:view", "abr:add", "abr:page"
        ),
    )


async def _show_branch(
    callback: CallbackQuery, session: AsyncSession, branch_id: int
) -> None:
    branch = await session.get(Branch, branch_id)
    if branch is None:
        await answer_callback(callback, "Filial topilmadi", True)
        return
    text = f"🏫 <b>{escape(branch.name)}</b>\nHolati: {'✅ Faol' if branch.is_active else '⛔ Faol emas'}"
    await edit_or_send(callback, text, branch_detail_kb(branch.id, branch.is_active))
    await answer_callback(callback)


@router.callback_query(F.data.startswith("abr:view:"))
async def branch_view(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_branch(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("abr:rename:"))
async def branch_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    branch_id = int(callback.data.split(":")[2])
    await state.update_data(branch_id=branch_id)
    await state.set_state(BranchForm.rename)
    await edit_or_send(
        callback, "✏️ Filialning yangi nomini yuboring:", cancel_admin_kb()
    )
    await answer_callback(callback)


@router.message(BranchForm.rename)
async def branch_rename_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    branch = await session.get(Branch, data["branch_id"])
    if branch is None:
        await state.clear()
        await message.answer("❌ Filial topilmadi")
        return
    try:
        await rename_branch(session, branch, message.text or "")
    except ValueError as exc:
        await message.answer(
            f"❌ {escape(str(exc))}\nBoshqa nom yuboring:",
            reply_markup=cancel_admin_kb(),
        )
        return
    await state.clear()
    await message.answer("✅ Filial nomi yangilandi.")


@router.callback_query(F.data.startswith("abr:toggle:"))
async def branch_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    branch = await session.get(Branch, int(callback.data.split(":")[2]))
    if branch:
        await toggle_branch(session, branch)
        await _show_branch(callback, session, branch.id)
        return
    await answer_callback(callback, "Filial topilmadi", True)


@router.callback_query(F.data.startswith("abr:delete:"))
async def branch_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    branch = await session.get(Branch, int(callback.data.split(":")[2]))
    if branch is None:
        await answer_callback(callback, "Filial topilmadi", True)
        return
    try:
        await delete_branch(session, branch)
    except ValueError as exc:
        await answer_callback(callback, str(exc), True)
        return
    await _show_list(callback, session)
    await answer_callback(callback, "Filial o‘chirildi")
