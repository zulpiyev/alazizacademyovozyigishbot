from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CompetitionBranch,
    CompetitionCategory,
    CompetitionSubject,
    Student,
    User,
    Vote,
)
from app.services.competition_service import get_main_competition
from app.utils.time import competition_status, utc_now


class VoteError(Exception):
    """Base voting-domain exception."""


class AlreadyVotedError(VoteError):
    """Raised when a Telegram user already voted in the selected group."""


class VotingClosedError(VoteError):
    """Raised when the competition is not accepting votes."""


class StudentUnavailableError(VoteError):
    """Raised when the selected student cannot receive a vote."""


async def upsert_user(session: AsyncSession, tg_user) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == tg_user.id))
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
            language_code=tg_user.language_code,
            last_seen_at=utc_now(),
        )
        session.add(user)
    else:
        user.username = tg_user.username
        user.full_name = tg_user.full_name
        user.language_code = tg_user.language_code
        user.last_seen_at = utc_now()
        user.is_blocked = False
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        user = await session.scalar(select(User).where(User.telegram_id == tg_user.id))
        if user is None:
            raise
    return user


async def has_voted(
    session: AsyncSession,
    telegram_id: int,
    competition_id: int,
    subject_id: int | None = None,
    category: str | None = None,
) -> bool:
    """Check whether a user has voted.

    When subject_id and category are supplied, the check is limited to that
    Fan + Sinf group. Without them it answers whether the user has cast any
    vote in the competition.
    """
    filters = [
        Vote.telegram_id == telegram_id,
        Vote.competition_id == competition_id,
    ]
    if subject_id is not None:
        filters.append(Vote.subject_id == subject_id)
    if category is not None:
        filters.append(Vote.category == category)
    return bool(await session.scalar(select(Vote.id).where(*filters).limit(1)))


async def cast_vote(session: AsyncSession, tg_user, student_id: int) -> Vote:
    competition = await get_main_competition(session)
    if (
        competition is None
        or competition_status(
            competition.state, competition.starts_at, competition.ends_at
        )
        != "active"
    ):
        raise VotingClosedError("Ovoz berish hozir faol emas")

    student = await session.scalar(
        select(Student)
        .options(selectinload(Student.branch), selectinload(Student.subject))
        .where(Student.id == student_id, Student.is_active.is_(True))
    )
    if student is None:
        raise StudentUnavailableError("O‘quvchi topilmadi yoki faol emas")

    branch_ok = await session.scalar(
        select(CompetitionBranch.id).where(
            CompetitionBranch.competition_id == competition.id,
            CompetitionBranch.branch_id == student.branch_id,
        )
    )
    subject_ok = await session.scalar(
        select(CompetitionSubject.id).where(
            CompetitionSubject.competition_id == competition.id,
            CompetitionSubject.subject_id == student.subject_id,
        )
    )
    category_ok = await session.scalar(
        select(CompetitionCategory.id).where(
            CompetitionCategory.competition_id == competition.id,
            CompetitionCategory.category == student.category,
        )
    )
    if not all((branch_ok, subject_ok, category_ok)):
        raise StudentUnavailableError("O‘quvchi ushbu tanlovda qatnashmaydi")

    competition_id = competition.id
    subject_id = student.subject_id
    category = student.category

    # Bir foydalanuvchi har bir Fan + Sinf guruhida faqat bir marta ovoz beradi.
    if await has_voted(
        session,
        tg_user.id,
        competition_id,
        subject_id=subject_id,
        category=category,
    ):
        raise AlreadyVotedError("Bu fan va sinf bo‘yicha avval ovoz bergansiz")

    user = await session.scalar(select(User).where(User.telegram_id == tg_user.id))
    vote = Vote(
        user_id=user.id if user else None,
        telegram_id=tg_user.id,
        student_id=student.id,
        competition_id=competition_id,
        branch_id=student.branch_id,
        subject_id=subject_id,
        category=category,
        username=tg_user.username,
        voter_full_name=tg_user.full_name,
    )
    session.add(vote)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if await has_voted(
            session,
            tg_user.id,
            competition_id,
            subject_id=subject_id,
            category=category,
        ):
            raise AlreadyVotedError(
                "Bu fan va sinf bo‘yicha avval ovoz bergansiz"
            ) from exc
        raise
    return vote


async def student_vote_result(
    session: AsyncSession,
    competition_id: int,
    student_id: int,
    branch_id: int | None,
    subject_id: int,
    category: str,
) -> tuple[int, int, float]:
    student_votes = (
        await session.scalar(
            select(func.count(Vote.id)).where(
                Vote.competition_id == competition_id,
                Vote.student_id == student_id,
            )
        )
        or 0
    )
    total_filters = [
        Vote.competition_id == competition_id,
        Vote.subject_id == subject_id,
        Vote.category == category,
    ]
    if branch_id is not None:
        total_filters.append(Vote.branch_id == branch_id)
    total_votes = (
        await session.scalar(select(func.count(Vote.id)).where(*total_filters)) or 0
    )
    percent = round(student_votes / total_votes * 100, 1) if total_votes else 0.0
    return student_votes, total_votes, percent
