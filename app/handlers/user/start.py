from __future__ import annotations

from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.keyboards.common import back_home_kb, main_menu_kb, subscription_kb
from app.services.competition_service import get_main_competition
from app.services.subscription_service import check_required_subscriptions
from app.services.vote_service import upsert_user
from app.utils.messages import answer_callback, edit_or_send
from app.utils.subscription_text import subscription_required_text
from app.utils.time import competition_status, format_local, remaining_text, status_label

router = Router(name="user_start")


async def _start_text_and_keyboard(
    session: AsyncSession, telegram_id: int, bot: Bot
):
    settings = get_settings()
    channels = settings.required_channels
    if channels:
        check = await check_required_subscriptions(bot, telegram_id, channels)
        if not check.subscribed:
            return (
                subscription_required_text(len(channels), check.check_failed),
                subscription_kb(channels, settings.instagram_name, settings.instagram_url),
            )

    competition = await get_main_competition(session)
    if competition is None:
        return (
            "❌ Hozircha tanlov mavjud emas.",
            main_menu_kb(voting_enabled=False),
        )

    status = competition_status(
        competition.state, competition.starts_at, competition.ends_at
    )
    if status == "finished":
        return (
            "🏆 <b>AL-AZIZ ACADEMY FILIALLARARO TANLOVI</b>\n\n"
            "⏰ <b>Vaqt tugadi!</b>\n\n"
            "Ovoz berish yakunlandi. Endi faqat statistikani ko‘rishingiz mumkin.",
            main_menu_kb(voting_enabled=False),
        )
    if status != "active":
        return (
            f"❌ Ovoz berish hozir faol emas.\n\nHolat: {status_label(status)}",
            main_menu_kb(voting_enabled=False),
        )

    text = (
        "🏆 <b>AL-AZIZ ACADEMY FILIALLARARO TANLOVI</b>\n\n"
        "Kerakli bo‘limni tanlang:\n\n"
        f"⏳ Qolgan vaqt: {remaining_text(competition.ends_at)}\n"
        f"🏁 Tugash vaqti: {format_local(competition.ends_at)}"
    )
    return text, main_menu_kb(voting_enabled=True)


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession) -> None:
    # Eski versiyadan qolgan pastki tugmalarni Telegram oynasidan olib tashlaydi.
    cleanup_message = await message.answer(
        "🔄 Menyu yangilanmoqda...", reply_markup=ReplyKeyboardRemove()
    )
    try:
        await cleanup_message.delete()
    except Exception:
        pass

    if message.from_user:
        await upsert_user(session, message.from_user)
        text, keyboard = await _start_text_and_keyboard(
            session, message.from_user.id, message.bot
        )
    else:
        text, keyboard = "❌ Foydalanuvchi ma’lumoti topilmadi.", main_menu_kb()
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "main:home")
async def home_handler(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    if callback.from_user:
        await upsert_user(session, callback.from_user)
        text, keyboard = await _start_text_and_keyboard(
            session, callback.from_user.id, callback.bot
        )
    else:
        text, keyboard = "❌ Foydalanuvchi ma’lumoti topilmadi.", main_menu_kb()
    await edit_or_send(callback, text, keyboard)
    await answer_callback(callback)


@router.callback_query(F.data == "subscription:check")
async def subscription_check_handler(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    if callback.from_user:
        await upsert_user(session, callback.from_user)
        text, keyboard = await _start_text_and_keyboard(
            session, callback.from_user.id, callback.bot
        )
    else:
        text, keyboard = (
            "❌ Foydalanuvchi ma’lumoti topilmadi.",
            main_menu_kb(voting_enabled=False),
        )
    await edit_or_send(callback, text, keyboard)
    await answer_callback(callback)


@router.callback_query(F.data == "main:about")
async def about_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_main_competition(session)
    if competition is None:
        text = (
            "ℹ️ <b>Tanlov haqida</b>\n\n"
            "Hozircha tanlov yaratilmagan. Tanlov admin tomonidan faollashtirilgach ovoz berish boshlanadi."
        )
    else:
        status = competition_status(
            competition.state, competition.starts_at, competition.ends_at
        )
        text = (
            f"ℹ️ <b>{escape(competition.name)}</b>\n\n"
            f"{escape(competition.description or 'Al-Aziz Academy o‘quvchilari o‘rtasidagi tanlov.')}\n\n"
            f"🕐 Boshlanish: {format_local(competition.starts_at)}\n"
            f"🏁 Tugash: {format_local(competition.ends_at)}\n"
            f"📌 Holat: {status_label(status)}\n"
        )
        if status == "active":
            text += f"⏳ Qolgan vaqt: {remaining_text(competition.ends_at)}\n"
        text += "\nHar bir Telegram foydalanuvchisi har bir fan va sinf bo‘yicha faqat bir marta ovoz bera oladi."
    await edit_or_send(callback, text, back_home_kb("main:home"))
    await answer_callback(callback)


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    await answer_callback(callback)
