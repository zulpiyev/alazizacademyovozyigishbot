from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.filters.admin import IsAdmin
from app.models import Admin, Branch, Student, Subject
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_settings")
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "adm:settings")
async def settings_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = get_settings()
    branch_count = await session.scalar(select(func.count(Branch.id))) or 0
    subject_count = await session.scalar(select(func.count(Subject.id))) or 0
    student_count = await session.scalar(select(func.count(Student.id))) or 0
    admin_count = await session.scalar(select(func.count(Admin.id))) or 0
    text = (
        "⚙️ <b>SOZLAMALAR</b>\n\n"
        f"🌍 Vaqt zonasi: {settings.timezone}\n"
        f"👮 Adminlar: {admin_count}\n"
        f"🏫 Filiallar: {branch_count}\n"
        f"📚 Fanlar: {subject_count}\n"
        f"👥 O‘quvchilar: {student_count}\n\n"
        "Admin kirish huquqi .env faylidagi ADMIN_IDS orqali boshqariladi."
    )
    await edit_or_send(
        callback,
        text,
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:home")]
            ]
        ),
    )
    await answer_callback(callback)
