from __future__ import annotations

from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


STUDENT_PAGE_SIZE = 80
BRANCH_PAGE_SIZE = 10


def branches_kb(
    branches,
    prefix: str,
    page: int = 0,
    back: str | None = "main:home",
    show_home: bool = True,
    show_user_tools: bool = False,
) -> InlineKeyboardMarkup:
    """Eski/admin yordamchi klaviatura. Foydalanuvchi oqimida ishlatilmaydi."""
    builder = InlineKeyboardBuilder()
    start = page * BRANCH_PAGE_SIZE
    chunk = branches[start : start + BRANCH_PAGE_SIZE]
    for branch in chunk:
        builder.button(
            text=f"🏫 {branch.name}", callback_data=f"{prefix}:{branch.id}:0"
        )
    builder.adjust(1)
    total_pages = max(1, ceil(len(branches) / BRANCH_PAGE_SIZE))
    if total_pages > 1:
        navigation = []
        if page > 0:
            navigation.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}p:{page - 1}")
            )
        navigation.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
        if page + 1 < total_pages:
            navigation.append(
                InlineKeyboardButton(text="➡️", callback_data=f"{prefix}p:{page + 1}")
            )
        builder.row(*navigation)
    if back:
        builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back))
    if show_user_tools:
        builder.row(
            InlineKeyboardButton(
                text="📊 Statistikani ko‘rish", callback_data="main:stats"
            )
        )
        builder.row(
            InlineKeyboardButton(text="ℹ️ Tanlov haqida", callback_data="main:about")
        )
    if show_home:
        builder.row(
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")
        )
    return builder.as_markup()


def subjects_kb(subjects, prefix: str, back_callback: str) -> InlineKeyboardMarkup:
    """Filial tanlamasdan fanlarni bitta ustunda chiqaradi."""
    builder = InlineKeyboardBuilder()
    for subject in subjects:
        builder.button(
            text=f"📚 {subject.name}",
            callback_data=f"{prefix}:{subject.id}",
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback))
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home"))
    return builder.as_markup()


def categories_kb(
    subject_id: int, prefix: str, back_callback: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 1–6-sinflar",
                    callback_data=f"{prefix}:{subject_id}:1-6:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📗 7–11-sinflar",
                    callback_data=f"{prefix}:{subject_id}:7-11:0",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")],
        ]
    )


def students_list_kb(
    students, subject_id: int, category: str, page: int, total: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for student in students:
        # Filiallararo tanlov: ism-familiya yonida filiali ko‘rinadi.
        builder.button(
            text=f"🏫 {student.branch.name} — {student.full_name}",
            callback_data=f"vcast:{student.id}",
        )
    builder.adjust(1)
    total_pages = max(1, ceil(total / STUDENT_PAGE_SIZE))
    if total_pages > 1:
        navigation = []
        if page > 0:
            navigation.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"vlist:{subject_id}:{category}:{page - 1}",
                )
            )
        navigation.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}", callback_data="noop"
            )
        )
        if (page + 1) * STUDENT_PAGE_SIZE < total:
            navigation.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"vlist:{subject_id}:{category}:{page + 1}",
                )
            )
        builder.row(*navigation)
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"vcat:{subject_id}")
    )
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home"))
    return builder.as_markup()


def student_card_kb(
    student, page: int, total_in_group: int, position: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ovoz berish", callback_data=f"vconfirm:{student.id}:{page}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Keyingi o‘quvchi",
                    callback_data=f"vnext:{student.id}:{page}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data=f"vlist:{student.subject_id}:{student.category}:{page}",
                )
            ],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")],
        ]
    )


def stats_results_kb(
    subject_id: int,
    category: str,
    page: int,
    total: int,
    page_size: int = 10,
) -> InlineKeyboardMarkup:
    total_pages = max(1, ceil(total / page_size))
    rows: list[list[InlineKeyboardButton]] = []
    navigation: list[InlineKeyboardButton] = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"sshow:{subject_id}:{category}:{page - 1}",
            )
        )
    navigation.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    if page + 1 < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"sshow:{subject_id}:{category}:{page + 1}",
            )
        )
    rows.append(navigation)
    rows.append(
        [
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data=f"sshow:{subject_id}:{category}:{page}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga", callback_data=f"scat:{subject_id}"
            )
        ]
    )
    rows.append([InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
