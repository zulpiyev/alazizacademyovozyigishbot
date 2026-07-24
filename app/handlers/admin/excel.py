from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin import IsAdmin
from app.keyboards.admin import excel_import_kb
from app.keyboards.common import cancel_admin_kb
from app.services.competition_service import get_main_competition
from app.services.excel_service import (
    build_import_template,
    export_results,
    export_top3_results,
    import_students,
)
from app.states.admin import ExcelImport
from app.utils.messages import answer_callback, edit_or_send

router = Router(name="admin_excel")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("result"))
async def result_command(message: Message, session: AsyncSession) -> None:
    """Admin uchun sovrinli o‘rinlar va fanlar bo‘yicha to‘liq Excel."""
    competition = await get_main_competition(session)
    if competition is None:
        await message.answer("❌ Natija uchun tanlov topilmadi.")
        return
    content = await export_top3_results(session, competition)
    await message.answer_document(
        BufferedInputFile(
            content, filename=f"toliq_natijalar_{competition.id}.xlsx"
        ),
        caption=(
            "🏆 <b>Fan va sinf bo‘yicha to‘liq natijalar</b>\n"
            "Excel ichida 1–2–3-o‘rinlar va har bir fan uchun alohida varaq mavjud. "
            "Fan varaqlarida barcha o‘quvchilar, ovozlar va foizlar ko‘rsatiladi."
        ),
    )


@router.callback_query(F.data == "adm:import")
async def excel_import_menu(callback: CallbackQuery) -> None:
    await edit_or_send(
        callback,
        "📥 <b>Excel orqali o‘quvchi yuklash</b>\n\n"
        "Ustunlar: Ism, Familiya, Filial, Fan, Sinf.",
        excel_import_kb(),
    )
    await answer_callback(callback)


@router.callback_query(F.data == "aex:template")
async def excel_template(callback: CallbackQuery) -> None:
    await callback.message.answer_document(
        BufferedInputFile(
            build_import_template(), filename="students_import_template.xlsx"
        ),
        caption="📄 O‘quvchilar importi uchun namuna",
    )
    await answer_callback(callback)


@router.callback_query(F.data == "aex:upload")
async def excel_upload_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ExcelImport.file)
    await edit_or_send(callback, "📎 .xlsx faylni yuboring:", cancel_admin_kb())
    await answer_callback(callback)


@router.message(ExcelImport.file, F.document)
async def excel_upload_finish(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    document = message.document
    if not document.file_name or not document.file_name.lower().endswith(".xlsx"):
        await message.answer("❌ Faqat .xlsx fayl yuboring.")
        return
    stream = await bot.download(document)
    if stream is None:
        await message.answer("❌ Faylni yuklab bo‘lmadi.")
        return
    stream.seek(0)
    try:
        added, errors = await import_students(session, stream.read())
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return
    await state.clear()
    await message.answer(f"✅ Import yakunlandi.\nQo‘shildi: {added} ta")
    if errors:
        await message.answer_document(
            BufferedInputFile(errors, filename="import_xatolari.xlsx"),
            caption="⚠️ Xato qatorlar alohida faylda",
        )


@router.message(ExcelImport.file)
async def excel_upload_invalid(message: Message) -> None:
    await message.answer("❌ .xlsx hujjat yuboring.")


@router.callback_query(F.data == "adm:export")
async def excel_export(callback: CallbackQuery, session: AsyncSession) -> None:
    competition = await get_main_competition(session)
    if competition is None:
        await answer_callback(callback, "Hisobot uchun tanlov topilmadi", True)
        return
    content = await export_results(session, competition)
    await callback.message.answer_document(
        BufferedInputFile(content, filename=f"natijalar_{competition.id}.xlsx"),
        caption=f"📊 {competition.name} natijalari",
    )
    await answer_callback(callback)
