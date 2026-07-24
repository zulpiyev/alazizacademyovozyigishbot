from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(voting_enabled: bool = True) -> InlineKeyboardMarkup:
    """Bosh menyu. Muddat tugagach faqat statistika tugmasi qoladi."""
    builder = InlineKeyboardBuilder()
    if voting_enabled:
        builder.button(text="🗳 Ovoz berish", callback_data="main:vote")
    builder.button(text="📊 Statistika", callback_data="main:stats")
    builder.adjust(1)
    return builder.as_markup()


def back_home_kb(back_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")],
        ]
    )


def confirm_kb(confirm_callback: str, cancel_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha, ovoz beraman", callback_data=confirm_callback
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish", callback_data=cancel_callback
                )
            ],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")],
        ]
    )


def cancel_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:home")]
        ]
    )


def subscription_kb(channels) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index, channel in enumerate(channels, start=1):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"➕ {index}. {channel.name}",
                    url=channel.url,
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="✅ Obunani tekshirish",
                callback_data="subscription:check",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
