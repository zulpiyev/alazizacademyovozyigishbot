from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin import IsAdmin
from app.keyboards.common import cancel_admin_kb
from app.services.broadcast_service import broadcast_copy
from app.states.admin import BroadcastForm
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_broadcasts")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "adm:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastForm.message)
    await edit_or_send(
        callback,
        "📢 Barcha foydalanuvchilarga yuboriladigan matn, rasm+matn yoki video+matnni yuboring:",
        cancel_admin_kb(),
    )
    await answer_callback(callback)


@router.message(BroadcastForm.message)
async def broadcast_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    progress = await message.answer("⏳ Xabar yuborilmoqda...")
    sent, failed = await broadcast_copy(
        message.bot,
        session,
        message,
        message.from_user.id,
    )
    await state.clear()
    await progress.edit_text(
        f"✅ Yuborish yakunlandi.\nYetkazildi: {sent}\nXato/blok: {failed}"
    )
