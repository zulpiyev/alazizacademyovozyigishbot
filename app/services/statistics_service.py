from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Branch, Competition, Student, Subject, User, Vote
from app.utils.time import to_local, utc_now


@dataclass(slots=True)
class RankedStudent:
    student: Student
    votes: int
    percent: float
    rank: int


async def group_results(
    session: AsyncSession,
    competition_id: int,
    branch_id: int | None,
    subject_id: int,
    category: str,
) -> tuple[list[RankedStudent], int]:
    filters = [
        Student.subject_id == subject_id,
        Student.category == category,
        Student.is_active.is_(True),
    ]
    if branch_id is not None:
        filters.append(Student.branch_id == branch_id)
    stmt = (
        select(Student, func.count(Vote.id).label("vote_count"))
        .outerjoin(
            Vote,
            (Vote.student_id == Student.id) & (Vote.competition_id == competition_id),
        )
        .options(selectinload(Student.branch), selectinload(Student.subject))
        .where(*filters)
        .group_by(Student.id)
        .order_by(
            func.count(Vote.id).desc(),
            Student.branch_id,
            Student.last_name,
            Student.first_name,
        )
    )
    rows = (await session.execute(stmt)).all()
    total = sum(int(row.vote_count) for row in rows)
    results: list[RankedStudent] = []
    previous_votes: int | None = None
    current_rank = 0
    for index, row in enumerate(rows, start=1):
        votes = int(row.vote_count)
        if previous_votes is None or votes < previous_votes:
            current_rank = index
        previous_votes = votes
        results.append(
            RankedStudent(
                student=row.Student,
                votes=votes,
                percent=round(votes / total * 100, 1) if total else 0.0,
                rank=current_rank,
            )
        )
    return results, total


async def admin_overview(
    session: AsyncSession, competition: Competition | None
) -> dict[str, object]:
    total_users = await session.scalar(select(func.count(User.id))) or 0
    voted_users = 0
    total_votes = 0
    today_votes = 0
    top = None
    if competition:
        total_votes = (
            await session.scalar(
                select(func.count(Vote.id)).where(Vote.competition_id == competition.id)
            )
            or 0
        )
        voted_users = (
            await session.scalar(
                select(func.count(func.distinct(Vote.telegram_id))).where(
                    Vote.competition_id == competition.id
                )
            )
            or 0
        )
        start_today = (
            to_local(utc_now())
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .astimezone(UTC)
        )
        today_votes = (
            await session.scalar(
                select(func.count(Vote.id)).where(
                    Vote.competition_id == competition.id,
                    Vote.voted_at >= start_today,
                )
            )
            or 0
        )
        top = await session.execute(
            select(Student, func.count(Vote.id).label("votes"))
            .join(Vote, Vote.student_id == Student.id)
            .options(selectinload(Student.branch), selectinload(Student.subject))
            .where(Vote.competition_id == competition.id)
            .group_by(Student.id)
            .order_by(func.count(Vote.id).desc())
            .limit(1)
        )
        top = top.first()
    return {
        "total_users": total_users,
        "voted_users": voted_users,
        "not_voted_users": max(0, total_users - voted_users),
        "total_votes": total_votes,
        "today_votes": today_votes,
        "top": top,
    }


async def breakdown_counts(session: AsyncSession, competition_id: int, dimension: str):
    if dimension == "branch":
        stmt = (
            select(Branch.name, func.count(Vote.id))
            .join(Vote, Vote.branch_id == Branch.id)
            .where(Vote.competition_id == competition_id)
            .group_by(Branch.id)
            .order_by(func.count(Vote.id).desc())
        )
    elif dimension == "subject":
        stmt = (
            select(Subject.name, func.count(Vote.id))
            .join(Vote, Vote.subject_id == Subject.id)
            .where(Vote.competition_id == competition_id)
            .group_by(Subject.id)
            .order_by(func.count(Vote.id).desc())
        )
    elif dimension == "category":
        stmt = (
            select(Student.category, func.count(Vote.id))
            .join(Student, Student.id == Vote.student_id)
            .where(Vote.competition_id == competition_id)
            .group_by(Student.category)
            .order_by(func.count(Vote.id).desc())
        )
    else:
        raise ValueError("Noto‘g‘ri kesim")
    return (await session.execute(stmt)).all()


async def time_series(session: AsyncSession, competition_id: int, hours: bool = False):
    dialect_name = session.get_bind().dialect.name
    if hours:
        since = utc_now() - timedelta(hours=24)
        bucket = (
            func.strftime("%Y-%m-%d %H:00:00", Vote.voted_at)
            if dialect_name == "sqlite"
            else func.date_trunc("hour", Vote.voted_at)
        )
    else:
        since = utc_now() - timedelta(days=14)
        bucket = (
            func.strftime("%Y-%m-%d 00:00:00", Vote.voted_at)
            if dialect_name == "sqlite"
            else func.date_trunc("day", Vote.voted_at)
        )
    stmt = (
        select(bucket.label("bucket"), func.count(Vote.id))
        .where(Vote.competition_id == competition_id, Vote.voted_at >= since)
        .group_by(bucket)
        .order_by(bucket)
    )
    rows = (await session.execute(stmt)).all()
    if dialect_name == "sqlite":
        return [(datetime.fromisoformat(str(value)), count) for value, count in rows]
    return rows
