from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def edit_or_send(
    event: CallbackQuery | Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    message = event.message if isinstance(event, CallbackQuery) else event
    if message is None:
        raise RuntimeError("Xabar topilmadi")
    try:
        if message.photo or message.video or message.document:
            await message.delete()
            return await message.bot.send_message(
                chat_id=message.chat.id, text=text, reply_markup=reply_markup
            )
        return await message.edit_text(text=text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return message
        return await message.answer(text=text, reply_markup=reply_markup)


async def send_below(
    event: CallbackQuery | Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    """Oldingi xabarni o‘zgartirmasdan yangi xabarni pastiga yuboradi."""
    message = event.message if isinstance(event, CallbackQuery) else event
    if message is None:
        raise RuntimeError("Xabar topilmadi")
    return await message.answer(text=text, reply_markup=reply_markup)


async def answer_callback(
    callback: CallbackQuery, text: str | None = None, show_alert: bool = False
) -> None:
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except TelegramBadRequest:
        return
