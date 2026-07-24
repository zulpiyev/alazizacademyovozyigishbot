from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.filters.admin import IsAdmin
from app.keyboards.admin import admin_menu_kb
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_panel")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def admin_command(message: Message) -> None:
    await message.answer(
        "⚙️ <b>ADMIN PANEL</b>\n\nKerakli bo‘limni tanlang.",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "adm:home")
async def admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_or_send(
        callback, "⚙️ <b>ADMIN PANEL</b>\n\nKerakli bo‘limni tanlang.", admin_menu_kb()
    )
    await answer_callback(callback)
