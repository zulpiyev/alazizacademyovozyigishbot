from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import BRANCHES, CATEGORY_PRIMARY, CATEGORY_SECONDARY, SUBJECTS
from app.models import (
    Branch,
    Competition,
    CompetitionBranch,
    CompetitionCategory,
    CompetitionSubject,
    Student,
    Subject,
)
from app.utils.time import competition_status, duration_end, ensure_utc, utc_now


async def get_main_competition(session: AsyncSession) -> Competition | None:
    stmt = (
        select(Competition)
        .where(Competition.is_main.is_(True))
        .order_by(Competition.created_at.desc())
        .limit(1)
    )
    competition = await session.scalar(stmt)
    if competition:
        return competition
    return await session.scalar(
        select(Competition).order_by(Competition.created_at.desc()).limit(1)
    )


async def get_competition(
    session: AsyncSession, competition_id: int
) -> Competition | None:
    return await session.get(Competition, competition_id)


async def list_competitions(session: AsyncSession) -> list[Competition]:
    return list(
        (
            await session.scalars(
                select(Competition).order_by(Competition.created_at.desc())
            )
        ).all()
    )


async def create_competition(
    session: AsyncSession,
    name: str,
    description: str | None,
    starts_at,
    duration_days: int,
) -> Competition:
    competition = Competition(
        name=name.strip(),
        description=description.strip() if description else None,
        starts_at=starts_at,
        ends_at=duration_end(starts_at, duration_days),
        duration_days=duration_days,
        state="scheduled",
        is_main=False,
    )
    session.add(competition)
    await session.flush()

    branch_ids = (
        await session.scalars(select(Branch.id).where(Branch.is_active.is_(True)))
    ).all()
    subject_ids = (
        await session.scalars(select(Subject.id).where(Subject.is_active.is_(True)))
    ).all()
    session.add_all(
        [
            CompetitionBranch(competition_id=competition.id, branch_id=i)
            for i in branch_ids
        ]
    )
    session.add_all(
        [
            CompetitionSubject(competition_id=competition.id, subject_id=i)
            for i in subject_ids
        ]
    )
    session.add_all(
        [
            CompetitionCategory(
                competition_id=competition.id, category=CATEGORY_PRIMARY
            ),
            CompetitionCategory(
                competition_id=competition.id, category=CATEGORY_SECONDARY
            ),
        ]
    )
    await session.commit()
    return competition


async def set_main_and_start(session: AsyncSession, competition: Competition) -> None:
    now = utc_now()
    await session.execute(select(Competition.id).with_for_update())
    await session.execute(update(Competition).values(is_main=False))
    competition.is_main = True
    competition.starts_at = ensure_utc(competition.starts_at)
    competition.ends_at = ensure_utc(competition.ends_at)
    if competition.starts_at > now:
        competition.state = "scheduled"
    elif competition.ends_at <= now:
        competition.starts_at = now
        competition.ends_at = now + timedelta(days=competition.duration_days)
        competition.state = "active"
    else:
        competition.state = "active"
    competition.paused_at = None
    await session.commit()


async def pause_competition(session: AsyncSession, competition: Competition) -> None:
    if (
        competition_status(
            competition.state, competition.starts_at, competition.ends_at
        )
        != "active"
    ):
        raise ValueError("Faqat faol tanlovni to‘xtatish mumkin")
    competition.state = "paused"
    competition.paused_at = utc_now()
    await session.commit()


async def resume_competition(session: AsyncSession, competition: Competition) -> None:
    if competition.state != "paused" or not competition.paused_at:
        raise ValueError("Tanlov vaqtincha to‘xtatilmagan")
    pause_duration = utc_now() - ensure_utc(competition.paused_at)
    competition.ends_at = ensure_utc(competition.ends_at) + pause_duration
    competition.state = "active"
    competition.paused_at = None
    await session.commit()


async def finish_competition(session: AsyncSession, competition: Competition) -> None:
    competition.state = "finished"
    if ensure_utc(competition.ends_at) > utc_now():
        competition.ends_at = utc_now()
    await session.commit()


async def delete_competition(session: AsyncSession, competition: Competition) -> None:
    await session.delete(competition)
    await session.commit()


async def participating_branches(
    session: AsyncSession, competition_id: int
) -> list[Branch]:
    stmt = (
        select(Branch)
        .join(CompetitionBranch, CompetitionBranch.branch_id == Branch.id)
        .where(
            CompetitionBranch.competition_id == competition_id,
            Branch.is_active.is_(True),
        )
        .order_by(Branch.name)
    )
    branches = list((await session.scalars(stmt)).all())
    order = {name: index for index, name in enumerate(BRANCHES)}
    branches.sort(key=lambda item: (order.get(item.name, len(order)), item.name))
    return branches


async def participating_subjects(
    session: AsyncSession, competition_id: int, branch_id: int | None = None
) -> list[Subject]:
    from app.models import BranchSubject

    stmt = (
        select(Subject)
        .join(CompetitionSubject, CompetitionSubject.subject_id == Subject.id)
        .where(
            CompetitionSubject.competition_id == competition_id,
            Subject.is_active.is_(True),
        )
    )
    if branch_id is not None:
        stmt = stmt.join(
            BranchSubject,
            (BranchSubject.subject_id == Subject.id)
            & (BranchSubject.branch_id == branch_id),
        ).where(BranchSubject.is_active.is_(True))
    subjects = list((await session.scalars(stmt.distinct())).all())
    order = {name: index for index, name in enumerate(SUBJECTS)}
    subjects.sort(key=lambda item: (order.get(item.name, len(order)), item.name))
    return subjects


async def available_student_categories(
    session: AsyncSession, branch_id: int, subject_id: int
) -> list[str]:
    categories = set(
        (
            await session.scalars(
                select(Student.category).where(
                    Student.branch_id == branch_id,
                    Student.subject_id == subject_id,
                    Student.is_active.is_(True),
                ).distinct()
            )
        ).all()
    )
    return [
        category
        for category in (CATEGORY_PRIMARY, CATEGORY_SECONDARY)
        if category in categories
    ]


async def participating_categories(
    session: AsyncSession, competition_id: int
) -> list[str]:
    stmt = select(CompetitionCategory.category).where(
        CompetitionCategory.competition_id == competition_id
    )
    return list((await session.scalars(stmt)).all())


async def toggle_competition_branch(
    session: AsyncSession, competition_id: int, branch_id: int
) -> bool:
    link = await session.scalar(
        select(CompetitionBranch).where(
            CompetitionBranch.competition_id == competition_id,
            CompetitionBranch.branch_id == branch_id,
        )
    )
    if link:
        await session.delete(link)
        enabled = False
    else:
        session.add(
            CompetitionBranch(competition_id=competition_id, branch_id=branch_id)
        )
        enabled = True
    await session.commit()
    return enabled


async def toggle_competition_subject(
    session: AsyncSession, competition_id: int, subject_id: int
) -> bool:
    link = await session.scalar(
        select(CompetitionSubject).where(
            CompetitionSubject.competition_id == competition_id,
            CompetitionSubject.subject_id == subject_id,
        )
    )
    if link:
        await session.delete(link)
        enabled = False
    else:
        session.add(
            CompetitionSubject(competition_id=competition_id, subject_id=subject_id)
        )
        enabled = True
    await session.commit()
    return enabled


async def toggle_competition_category(
    session: AsyncSession, competition_id: int, category: str
) -> bool:
    link = await session.scalar(
        select(CompetitionCategory).where(
            CompetitionCategory.competition_id == competition_id,
            CompetitionCategory.category == category,
        )
    )
    if link:
        await session.delete(link)
        enabled = False
    else:
        session.add(
            CompetitionCategory(competition_id=competition_id, category=category)
        )
        enabled = True
    await session.commit()
    return enabled
