from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import CATEGORY_LABELS
from app.keyboards.common import subscription_kb
from app.keyboards.user import (
    STUDENT_PAGE_SIZE,
    categories_kb,
    students_list_kb,
    subjects_kb,
)
from app.services.admin_service import get_student, list_students
from app.services.competition_service import get_main_competition, participating_subjects
from app.services.statistics_service import group_results
from app.services.subscription_service import check_required_subscriptions
from app.services.vote_service import (
    AlreadyVotedError,
    StudentUnavailableError,
    VotingClosedError,
    cast_vote,
)
from app.utils.competition_text import step_text
from app.utils.messages import answer_callback, send_below
from app.utils.percent_card import percent_card_row
from app.utils.result_chunks import split_result_text
from app.utils.subscription_text import subscription_required_text
from app.utils.time import competition_status, status_label

router = Router(name="user_voting")


async def _require_subscription(callback: CallbackQuery) -> bool:
    settings = get_settings()
    channels = settings.required_channels
    if not channels:
        return True

    check = await check_required_subscriptions(
        callback.bot, callback.from_user.id, channels
    )
    if check.subscribed:
        return True

    await send_below(
        callback,
        subscription_required_text(len(channels), check.check_failed),
        subscription_kb(channels),
    )
    await answer_callback(
        callback,
        "Avval ikkala kanalga obuna bo‘ling",
        True,
    )
    return False


def _closed_voting_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistikani ko‘rish", callback_data="main:stats")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")],
        ]
    )


async def _show_voting_error(callback: CallbackQuery, error: str) -> None:
    await send_below(callback, error, _closed_voting_keyboard())
    await answer_callback(callback)


async def _active_competition(session: AsyncSession):
    competition = await get_main_competition(session)
    if competition is None:
        return None, "❌ Hozircha tanlov yaratilmagan."
    status = competition_status(
        competition.state, competition.starts_at, competition.ends_at
    )
    if status == "finished":
        return (
            competition,
            "⏰ <b>Vaqt tugadi!</b>\n\n"
            "Ovoz berish yakunlandi. Endi faqat statistikani ko‘rishingiz mumkin.",
        )
    if status != "active":
        return (
            competition,
            f"❌ Ovoz berish hozir faol emas.\n\nHolat: {status_label(status)}",
        )
    return competition, None


def _results_keyboard(subject_id: int, category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Natijani yangilash",
                    callback_data=f"vgroup:{subject_id}:{category}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Sinflarga qaytish", callback_data=f"vcat:{subject_id}"
                )
            ],
            [InlineKeyboardButton(text="📚 Fanlar", callback_data="main:vote")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main:home")],
        ]
    )


async def _group_results_chunks(
    session: AsyncSession,
    competition,
    subject_id: int,
    category: str,
    notice: str,
    selected_student=None,
) -> list[str]:
    results, _total = await group_results(
        session, competition.id, None, subject_id, category
    )

    header_lines = [
        notice,
        "",
        "╭──── 📊 <b>FOIZ NATIJALARI</b> ────╮",
    ]

    selected_id = getattr(selected_student, "id", None)
    result_blocks: list[str] = []
    if not results:
        result_blocks.append("│ Bu bo‘limda o‘quvchilar mavjud emas.")
    else:
        for item in results:
            result_blocks.append(
                percent_card_row(
                    item.student.full_name,
                    item.student.branch.name,
                    item.percent,
                    selected=item.student.id == selected_id,
                )
            )

    footer_lines = ["╰────────────────────────────╯"]
    return split_result_text(header_lines, result_blocks, footer_lines)


async def _show_group_results(
    callback: CallbackQuery,
    chunks: list[str],
    keyboard: InlineKeyboardMarkup,
) -> None:
    """Natijalarni oldingi xabarni o‘zgartirmasdan pastiga yuboradi."""
    if callback.message is None:
        return
    for index, chunk in enumerate(chunks):
        is_last = index == len(chunks) - 1
        await callback.message.answer(
            chunk, reply_markup=keyboard if is_last else None
        )


@router.callback_query(F.data == "main:vote")
async def vote_start(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _require_subscription(callback):
        return
    competition, error = await _active_competition(session)
    if error:
        await _show_voting_error(callback, error)
        return

    subjects = await participating_subjects(session, competition.id)
    text = step_text(
        "🏆 <b>FILIALLARARO O‘QUVCHILAR TANLOVI</b>",
        competition,
        "1️⃣ <b>Fanni tanlang</b>",
    )
    await send_below(callback, text, subjects_kb(subjects, "vsub", "main:home"))
    await answer_callback(callback)


async def _show_vote_categories(
    callback: CallbackQuery, session: AsyncSession, subject_id: int
) -> None:
    if not await _require_subscription(callback):
        return
    competition, error = await _active_competition(session)
    if error:
        await _show_voting_error(callback, error)
        return
    keyboard = categories_kb(subject_id, "vlist", "main:vote")
    await send_below(
        callback,
        step_text(
            "2️⃣ <b>Sinfni tanlang</b>",
            competition,
            "Kerakli sinf bo‘limini tanlang:",
        ),
        keyboard,
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("vsub:"))
async def vote_subject_selected(callback: CallbackQuery, session: AsyncSession) -> None:
    _, subject_raw = callback.data.split(":")
    await _show_vote_categories(callback, session, int(subject_raw))


@router.callback_query(F.data.startswith("vcat:"))
async def vote_category_back(callback: CallbackQuery, session: AsyncSession) -> None:
    _, subject_raw = callback.data.split(":")
    await _show_vote_categories(callback, session, int(subject_raw))


@router.callback_query(F.data.startswith("vlist:"))
async def vote_student_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _require_subscription(callback):
        return
    _, subject_raw, category, page_raw = callback.data.split(":")
    subject_id, page = int(subject_raw), int(page_raw)
    competition, error = await _active_competition(session)
    if error:
        await _show_voting_error(callback, error)
        return
    students, total = await list_students(
        session,
        page=page,
        page_size=STUDENT_PAGE_SIZE,
        branch_id=None,
        subject_id=subject_id,
        category=category,
        include_inactive=False,
    )
    text = step_text(
        "3️⃣ <b>O‘quvchini tanlang</b>",
        competition,
        (
            f"🎓 {CATEGORY_LABELS[category]}\n"
            f"👥 O‘quvchilar soni: {total} ta"
        ),
    )
    if not students:
        text += "\n\nBu bo‘limda faol o‘quvchi yo‘q."
    await send_below(
        callback,
        text,
        students_list_kb(students, subject_id, category, page, total),
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("vgroup:"))
async def vote_group_results(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _require_subscription(callback):
        return
    _, subject_raw, category = callback.data.split(":")
    competition, error = await _active_competition(session)
    if error:
        await _show_voting_error(callback, error)
        return
    subject_id = int(subject_raw)
    chunks = await _group_results_chunks(
        session,
        competition,
        subject_id,
        category,
        "📊 <b>Natijalar yangilandi</b>",
    )
    await _show_group_results(
        callback, chunks, _results_keyboard(subject_id, category)
    )
    await answer_callback(callback)


@router.callback_query(F.data.startswith("vcast:"))
async def vote_cast(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _require_subscription(callback):
        return
    student_id = int(callback.data.split(":")[1])
    student = await get_student(session, student_id)
    if student is None:
        await answer_callback(callback, "O‘quvchi topilmadi", True)
        return

    competition, error = await _active_competition(session)
    if error:
        await _show_voting_error(callback, error)
        return

    accepted = True
    try:
        await cast_vote(session, callback.from_user, student_id)
        notice = "✅ <b>Ovoz qabul qilindi!</b>"
    except AlreadyVotedError:
        accepted = False
        notice = (
            "❌ <b>Ovoz qabul qilinmadi!</b>\n"
            "Siz ushbu fan va sinf bo‘yicha avval ovoz bergansiz."
        )
    except VotingClosedError:
        await _show_voting_error(
            callback,
            "⏰ <b>Vaqt tugadi!</b>\n\n"
            "Ovoz berish yakunlandi. Endi faqat statistikani ko‘rishingiz mumkin.",
        )
        return
    except StudentUnavailableError as exc:
        await answer_callback(callback, f"❌ {exc}", True)
        return

    chunks = await _group_results_chunks(
        session,
        competition,
        student.subject_id,
        student.category,
        notice,
        selected_student=student if accepted else None,
    )
    await _show_group_results(
        callback,
        chunks,
        _results_keyboard(student.subject_id, student.category),
    )
    # Popup chiqarmaymiz: qabul qilindi/qilinmadi xabari natijalar bilan
    # birga chatning o‘zida ko‘rinadi.
    await answer_callback(callback)
