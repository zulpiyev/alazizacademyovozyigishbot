from unittest.mock import AsyncMock, MagicMock

from aiogram.types import CallbackQuery, Message

from app.utils.messages import send_below


async def test_send_below_keeps_old_message_and_sends_new_one():
    callback = MagicMock(spec=CallbackQuery)
    callback.message = MagicMock(spec=Message)
    callback.message.answer = AsyncMock(return_value=MagicMock(spec=Message))
    callback.message.edit_text = AsyncMock()

    keyboard = MagicMock()
    result = await send_below(callback, "Yangi bosqich", keyboard)

    callback.message.answer.assert_awaited_once_with(
        text="Yangi bosqich", reply_markup=keyboard
    )
    callback.message.edit_text.assert_not_awaited()
    assert result is callback.message.answer.return_value
