from __future__ import annotations

from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


ADMIN_PAGE_SIZE = 10


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🏫 Filiallar", "adm:branches"),
        ("📚 Fanlar", "adm:subjects"),
        ("👥 O‘quvchilar", "adm:students"),
        ("🗳 Tanlovlar", "adm:competitions"),
        ("📊 Statistika", "adm:stats"),
        ("📥 Excel orqali yuklash", "adm:import"),
        ("📤 Excel hisobot", "adm:export"),
        ("📢 Xabar yuborish", "adm:broadcast"),
        ("⚙️ Sozlamalar", "adm:settings"),
    ]
    for text, callback in buttons:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2, 2, 2, 2, 1)
    builder.row(
        InlineKeyboardButton(text="🏠 Foydalanuvchi menyusi", callback_data="main:home")
    )
    return builder.as_markup()


def entities_kb(
    items, detail_prefix: str, add_callback: str, page_callback: str, page: int = 0
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * ADMIN_PAGE_SIZE
    chunk = items[start : start + ADMIN_PAGE_SIZE]
    for item in chunk:
        status = "✅" if item.is_active else "⛔"
        builder.button(
            text=f"{status} {item.name}", callback_data=f"{detail_prefix}:{item.id}"
        )
    builder.adjust(1)
    total_pages = max(1, ceil(len(items) / ADMIN_PAGE_SIZE))
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"{page_callback}:{page - 1}")
        )
    nav.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    if page + 1 < total_pages:
        nav.append(
            InlineKeyboardButton(text="➡️", callback_data=f"{page_callback}:{page + 1}")
        )
    builder.row(*nav)
    builder.row(InlineKeyboardButton(text="➕ Qo‘shish", callback_data=add_callback))
    builder.row(InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:home"))
    return builder.as_markup()


def branch_detail_kb(branch_id: int, active: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Nomini o‘zgartirish",
                    callback_data=f"abr:rename:{branch_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ O‘chirish" if active else "✅ Faollashtirish",
                    callback_data=f"abr:toggle:{branch_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Butunlay o‘chirish", callback_data=f"abr:delete:{branch_id}"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:branches")],
        ]
    )


def subject_detail_kb(subject_id: int, active: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Nomini o‘zgartirish",
                    callback_data=f"asu:rename:{subject_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏫 Filiallarga biriktirish",
                    callback_data=f"asu:attach:{subject_id}:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ O‘chirish" if active else "✅ Faollashtirish",
                    callback_data=f"asu:toggle:{subject_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Butunlay o‘chirish",
                    callback_data=f"asu:delete:{subject_id}",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:subjects")],
        ]
    )


def student_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ O‘quvchi qo‘shish", callback_data="ast:add"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 O‘quvchilar ro‘yxati", callback_data="ast:list:0"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:home")],
        ]
    )


def students_admin_list_kb(students, page: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for student in students:
        status = "✅" if student.is_active else "⛔"
        builder.button(
            text=f"{status} {student.first_name} {student.last_name}",
            callback_data=f"ast:view:{student.id}",
        )
    builder.adjust(1)
    total_pages = max(1, ceil(total / ADMIN_PAGE_SIZE))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"ast:list:{page - 1}"))
    nav.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    if (page + 1) * ADMIN_PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"ast:list:{page + 1}"))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(text="➕ Qo‘shish", callback_data="ast:add"))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:students"))
    return builder.as_markup()


def student_detail_admin_kb(student_id: int, active: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Ism-familiya", callback_data=f"ast:rename:{student_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎓 Sinfni o‘zgartirish",
                    callback_data=f"ast:grade:{student_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏫 Filial/fanni o‘zgartirish",
                    callback_data=f"ast:move:{student_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ O‘chirish" if active else "✅ Faollashtirish",
                    callback_data=f"ast:toggle:{student_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Butunlay o‘chirish",
                    callback_data=f"ast:delete:{student_id}",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="ast:list:0")],
        ]
    )


def choose_items_kb(
    items, prefix: str, back_callback: str, selected_ids: set[int] | None = None
) -> InlineKeyboardMarkup:
    selected_ids = selected_ids or set()
    builder = InlineKeyboardBuilder()
    for item in items:
        mark = "✅" if item.id in selected_ids else "▫️"
        builder.button(text=f"{mark} {item.name}", callback_data=f"{prefix}:{item.id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback))
    return builder.as_markup()


def competition_list_kb(competitions) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for comp in competitions:
        main = "⭐" if comp.is_main else "▫️"
        builder.button(text=f"{main} {comp.name}", callback_data=f"acp:view:{comp.id}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="➕ Tanlov yaratish", callback_data="acp:add")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:home"))
    return builder.as_markup()


def competition_detail_kb(comp) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="▶️ Asosiy qilib boshlash", callback_data=f"acp:start:{comp.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏸ To‘xtatish", callback_data=f"acp:pause:{comp.id}"
            ),
            InlineKeyboardButton(
                text="▶️ Davom ettirish", callback_data=f"acp:resume:{comp.id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏹ Yakunlash", callback_data=f"acp:finish:{comp.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏫 Filiallar", callback_data=f"acp:branches:{comp.id}"
            ),
            InlineKeyboardButton(
                text="📚 Fanlar", callback_data=f"acp:subjects:{comp.id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎓 Toifalar", callback_data=f"acp:categories:{comp.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 O‘chirish", callback_data=f"acp:delete:{comp.id}"
            )
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:competitions")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def excel_import_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Namuna Excel", callback_data="aex:template"
                )
            ],
            [InlineKeyboardButton(text="📥 Fayl yuborish", callback_data="aex:upload")],
            [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:home")],
        ]
    )
