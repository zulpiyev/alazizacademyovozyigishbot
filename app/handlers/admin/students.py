from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin import IsAdmin
from app.keyboards.admin import (
    choose_items_kb,
    student_detail_admin_kb,
    student_menu_kb,
    students_admin_list_kb,
)
from app.keyboards.common import cancel_admin_kb
from app.models import Student
from app.services.admin_service import (
    create_student,
    get_student,
    list_branches,
    list_students,
    subjects_for_branch,
    toggle_student,
    update_student_grade,
    update_student_group,
    update_student_name,
    delete_student,
)
from app.states.admin import StudentAdd, StudentEdit
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_students")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "adm:students")
async def students_menu(callback: CallbackQuery) -> None:
    await edit_or_send(callback, "👥 <b>O‘quvchilar boshqaruvi</b>", student_menu_kb())
    await answer_callback(callback)


async def _show_students_page(
    callback: CallbackQuery, session: AsyncSession, page: int
) -> None:
    students, total = await list_students(session, page=page, page_size=10)
    await edit_or_send(
        callback,
        f"📋 <b>O‘quvchilar</b>\nJami: {total} ta",
        students_admin_list_kb(students, page, total),
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("ast:list:"))
async def students_list(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_students_page(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data == "ast:add")
async def student_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(StudentAdd.first_name)
    await edit_or_send(callback, "➕ O‘quvchining ismini yuboring:", cancel_admin_kb())
    await answer_callback(callback)


@router.message(StudentAdd.first_name)
async def student_add_first_name(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Ismni to‘g‘ri kiriting:")
        return
    await state.update_data(first_name=message.text.strip())
    await state.set_state(StudentAdd.last_name)
    await message.answer("Familiyasini yuboring:", reply_markup=cancel_admin_kb())


@router.message(StudentAdd.last_name)
async def student_add_last_name(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Familiyani to‘g‘ri kiriting:")
        return
    await state.update_data(last_name=message.text.strip())
    await state.set_state(StudentAdd.branch)
    branches = await list_branches(session, include_inactive=False)
    await message.answer(
        "🏫 Filialni tanlang:",
        reply_markup=choose_items_kb(branches, "asta:branch", "adm:students"),
    )


@router.callback_query(StudentAdd.branch, F.data.startswith("asta:branch:"))
async def student_add_branch(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    branch_id = int(callback.data.split(":")[2])
    await state.update_data(branch_id=branch_id)
    await state.set_state(StudentAdd.subject)
    subjects = await subjects_for_branch(session, branch_id)
    await edit_or_send(
        callback,
        "📚 Fanni tanlang:",
        choose_items_kb(subjects, "asta:subject", "adm:students"),
    )
    await answer_callback(callback)


@router.callback_query(StudentAdd.subject, F.data.startswith("asta:subject:"))
async def student_add_subject(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(subject_id=int(callback.data.split(":")[2]))
    await state.set_state(StudentAdd.grade)
    await edit_or_send(
        callback, "🎓 Sinfni 1 dan 11 gacha raqamda yuboring:", cancel_admin_kb()
    )
    await answer_callback(callback)


@router.message(StudentAdd.grade)
async def student_add_grade(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    try:
        grade = int(message.text or "")
        if not 1 <= grade <= 11:
            raise ValueError
    except ValueError:
        await message.answer("❌ Sinfni 1 dan 11 gacha raqamda yuboring:")
        return

    data = await state.get_data()
    try:
        student = await create_student(
            session,
            data["first_name"],
            data["last_name"],
            data["branch_id"],
            data["subject_id"],
            grade,
            None,
        )
    except ValueError as exc:
        await state.clear()
        await message.answer(f"❌ {escape(str(exc))}", reply_markup=student_menu_kb())
        return

    await state.clear()
    await message.answer(
        f"✅ {escape(student.full_name)} o‘quvchisi rasmsiz qo‘shildi.",
        reply_markup=student_menu_kb(),
    )


async def _show_student(
    callback: CallbackQuery, session: AsyncSession, student_id: int
) -> None:
    student = await get_student(session, student_id)
    if student is None:
        await answer_callback(callback, "O‘quvchi topilmadi", True)
        return
    text = (
        f"👤 <b>{escape(student.full_name)}</b>\n"
        f"🏫 {escape(student.branch.name)}\n"
        f"📚 {escape(student.subject.name)}\n"
        f"🎓 {student.grade}-sinf\n"
        f"Holati: {'✅ Faol' if student.is_active else '⛔ Faol emas'}"
    )
    await edit_or_send(
        callback, text, student_detail_admin_kb(student.id, student.is_active)
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("ast:view:"))
async def student_view(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_student(callback, session, int(callback.data.split(":")[2]))


@router.callback_query(F.data.startswith("ast:rename:"))
async def student_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(student_id=int(callback.data.split(":")[2]))
    await state.set_state(StudentEdit.rename)
    await edit_or_send(
        callback, "✏️ Yangi ism va familiyani bitta qatorda yuboring:", cancel_admin_kb()
    )
    await answer_callback(callback)


@router.message(StudentEdit.rename)
async def student_rename_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("❌ Ism va familiyani bitta qatorda yuboring:")
        return
    data = await state.get_data()
    student = await session.get(Student, data["student_id"])
    if student is None:
        await state.clear()
        await message.answer("❌ O‘quvchi topilmadi")
        return
    await update_student_name(session, student, parts[0], parts[1])
    await state.clear()
    await message.answer("✅ Ism-familiya yangilandi.")


@router.callback_query(F.data.startswith("ast:grade:"))
async def student_grade_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(student_id=int(callback.data.split(":")[2]))
    await state.set_state(StudentEdit.grade)
    await edit_or_send(
        callback, "🎓 Yangi sinfni 1 dan 11 gacha yuboring:", cancel_admin_kb()
    )
    await answer_callback(callback)


@router.message(StudentEdit.grade)
async def student_grade_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    try:
        grade = int(message.text or "")
        if not 1 <= grade <= 11:
            raise ValueError
    except ValueError:
        await message.answer("❌ Sinfni 1 dan 11 gacha yuboring:")
        return
    data = await state.get_data()
    student = await session.get(Student, data["student_id"])
    if student is None:
        await state.clear()
        await message.answer("❌ O‘quvchi topilmadi")
        return
    await update_student_grade(session, student, grade)
    await state.clear()
    await message.answer("✅ Sinf va toifa avtomatik yangilandi.")


@router.callback_query(F.data.startswith("ast:move:"))
async def student_move_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    student_id = int(callback.data.split(":")[2])
    await state.update_data(student_id=student_id)
    await state.set_state(StudentEdit.move_branch)
    branches = await list_branches(session, include_inactive=False)
    await edit_or_send(
        callback,
        "🏫 Yangi filialni tanlang:",
        choose_items_kb(
            branches, f"astm:branch:{student_id}", f"ast:view:{student_id}"
        ),
    )
    await answer_callback(callback)


@router.callback_query(StudentEdit.move_branch, F.data.startswith("astm:branch:"))
async def student_move_branch(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    _, _, student_raw, branch_raw = callback.data.split(":")
    branch_id = int(branch_raw)
    await state.update_data(branch_id=branch_id)
    await state.set_state(StudentEdit.move_subject)
    subjects = await subjects_for_branch(session, branch_id)
    await edit_or_send(
        callback,
        "📚 Yangi fanni tanlang:",
        choose_items_kb(
            subjects, f"astm:subject:{student_raw}", f"ast:view:{student_raw}"
        ),
    )
    await answer_callback(callback)


@router.callback_query(StudentEdit.move_subject, F.data.startswith("astm:subject:"))
async def student_move_subject(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    _, _, student_raw, subject_raw = callback.data.split(":")
    data = await state.get_data()
    student = await session.get(Student, int(student_raw))
    if student is None:
        await state.clear()
        await answer_callback(callback, "O‘quvchi topilmadi", True)
        return
    await update_student_group(session, student, data["branch_id"], int(subject_raw))
    await state.clear()
    await _show_student(callback, session, student.id)


@router.callback_query(F.data.startswith("ast:toggle:"))
async def student_toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    student = await session.get(Student, int(callback.data.split(":")[2]))
    if student:
        await toggle_student(session, student)
        await _show_student(callback, session, student.id)
        return
    await answer_callback(callback, "O‘quvchi topilmadi", True)


@router.callback_query(F.data.startswith("ast:delete:"))
async def student_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    student = await session.get(Student, int(callback.data.split(":")[2]))
    if student is None:
        await answer_callback(callback, "O‘quvchi topilmadi", True)
        return
    try:
        await delete_student(session, student)
    except Exception:
        await session.rollback()
        await answer_callback(
            callback, "O‘quvchida ovozlar bor. Uni faolsizlantiring.", True
        )
        return
    await _show_students_page(callback, session, 0)
