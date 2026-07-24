from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import BRANCHES, CATEGORY_PRIMARY, CATEGORY_SECONDARY, SUBJECTS
from app.data.default_students import DEFAULT_ROSTER_VERSION, DEFAULT_STUDENTS
from app.models import (
    Admin,
    Branch,
    BranchSubject,
    Competition,
    CompetitionBranch,
    CompetitionCategory,
    CompetitionSubject,
    Setting,
    Student,
    Subject,
    Vote,
)
from app.utils.time import utc_now


def _category_for_grade(grade: int) -> str:
    return CATEGORY_PRIMARY if grade <= 6 else CATEGORY_SECONDARY


async def _merge_it_subjects(session: AsyncSession) -> None:
    """Eski IT-dasturlash fanini IT faniga xavfsiz birlashtiradi.

    O‘quvchilar va oldingi ovozlar saqlanadi. Bir foydalanuvchi ilgari IT va
    IT-dasturlashning ikkalasida ham ovoz bergan bo‘lsa, birlashtirilgandan
    keyin takroriy bo‘lib qolmasligi uchun IT dagi avvalgi ovozi saqlanadi.
    """
    canonical = await session.scalar(
        select(Subject).where(func.lower(Subject.name) == "it").limit(1)
    )
    if canonical is None:
        canonical = Subject(name="IT", is_active=True)
        session.add(canonical)
        await session.flush()

    aliases = list(
        (
            await session.scalars(
                select(Subject).where(
                    func.lower(Subject.name).in_(
                        ("it-dasturlash", "it dasturlash", "it_dasturlash")
                    )
                )
            )
        ).all()
    )
    for alias in aliases:
        if alias.id == canonical.id:
            continue

        # Filial-fan bog‘lanishlarini dublikat qilmasdan IT ga ko‘chirish.
        branch_links = list(
            (
                await session.scalars(
                    select(BranchSubject).where(BranchSubject.subject_id == alias.id)
                )
            ).all()
        )
        for link in branch_links:
            target = await session.scalar(
                select(BranchSubject).where(
                    BranchSubject.branch_id == link.branch_id,
                    BranchSubject.subject_id == canonical.id,
                )
            )
            if target is not None:
                target.is_active = target.is_active or link.is_active
                await session.delete(link)
            else:
                link.subject_id = canonical.id
        await session.flush()

        # Tanlovdagi fan bog‘lanishlarini ham IT ga ko‘chirish.
        competition_links = list(
            (
                await session.scalars(
                    select(CompetitionSubject).where(
                        CompetitionSubject.subject_id == alias.id
                    )
                )
            ).all()
        )
        for link in competition_links:
            target = await session.scalar(
                select(CompetitionSubject).where(
                    CompetitionSubject.competition_id == link.competition_id,
                    CompetitionSubject.subject_id == canonical.id,
                )
            )
            if target is not None:
                await session.delete(link)
            else:
                link.subject_id = canonical.id
        await session.flush()

        # Avval takroriy bo‘lib qoladigan ovozlarni olib tashlaymiz.
        alias_votes = list(
            (await session.scalars(select(Vote).where(Vote.subject_id == alias.id))).all()
        )
        votes_to_move: list[Vote] = []
        for vote in alias_votes:
            existing_vote = await session.scalar(
                select(Vote.id).where(
                    Vote.telegram_id == vote.telegram_id,
                    Vote.competition_id == vote.competition_id,
                    Vote.subject_id == canonical.id,
                    Vote.category == vote.category,
                ).limit(1)
            )
            if existing_vote is not None:
                await session.delete(vote)
            else:
                votes_to_move.append(vote)
        await session.flush()
        for vote in votes_to_move:
            vote.subject_id = canonical.id

        # O‘quvchilar ayni sinf guruhida IT fani ostida ko‘rinadi.
        students = list(
            (
                await session.scalars(
                    select(Student).where(Student.subject_id == alias.id)
                )
            ).all()
        )
        for student in students:
            student.subject_id = canonical.id

        alias.is_active = False
        await session.flush()

    canonical.is_active = True


async def _seed_students(
    session: AsyncSession,
    branches_by_name: dict[str, Branch],
    subjects_by_name: dict[str, Subject],
) -> None:
    """Berilgan haqiqiy ro‘yxatni bazaga bir marta sinxronlaydi.

    Yangi ro‘yxat versiyasi kelganda avvalgi o‘quvchilar o‘chirilmaydi, balki
    nofaol qilinadi. Shu sababli eski ovozlar va statistika buzilmaydi.
    """
    marker = await session.scalar(
        select(Setting).where(Setting.key == "default_roster_version")
    )
    if marker is not None and marker.value == DEFAULT_ROSTER_VERSION:
        return

    existing_students = list((await session.scalars(select(Student))).all())
    existing_by_key = {
        (
            student.first_name.casefold(),
            student.last_name.casefold(),
            student.branch_id,
            student.subject_id,
            student.grade,
        ): student
        for student in existing_students
    }

    # Oldingi demo yoki eski ro‘yxatdagi o‘quvchilar ovozlar saqlanishi uchun
    # o‘chirilmaydi; faqat ovoz berish ro‘yxatidan yashiriladi.
    for student in existing_students:
        student.is_active = False

    for full_name, branch_name, subject_name, grade in DEFAULT_STUDENTS:
        branch = branches_by_name.get(branch_name)
        subject = subjects_by_name.get(subject_name)
        if branch is None or subject is None:
            continue

        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
        key = (
            first_name.casefold(),
            last_name.casefold(),
            branch.id,
            subject.id,
            grade,
        )
        student = existing_by_key.get(key)
        if student is None:
            student = Student(
                first_name=first_name,
                last_name=last_name,
                branch_id=branch.id,
                subject_id=subject.id,
                grade=grade,
                category=_category_for_grade(grade),
                photo_file_id=None,
                is_active=True,
            )
            session.add(student)
            existing_by_key[key] = student
        else:
            student.category = _category_for_grade(grade)
            student.is_active = True

    if marker is None:
        session.add(
            Setting(key="default_roster_version", value=DEFAULT_ROSTER_VERSION)
        )
    else:
        marker.value = DEFAULT_ROSTER_VERSION


async def seed_defaults(session: AsyncSession, settings: Settings) -> None:
    # Faqat yangi ro‘yxatda qatnashadigan filial va fanlar faol qoladi.
    await session.execute(
        update(Branch).where(Branch.name.not_in(BRANCHES)).values(is_active=False)
    )
    await session.execute(
        update(Branch).where(Branch.name.in_(BRANCHES)).values(is_active=True)
    )
    await session.execute(
        update(Subject).where(Subject.name.not_in(SUBJECTS)).values(is_active=False)
    )
    await session.execute(
        update(Subject).where(Subject.name.in_(SUBJECTS)).values(is_active=True)
    )

    existing_branches = set((await session.scalars(select(Branch.name))).all())
    for name in BRANCHES:
        if name not in existing_branches:
            session.add(Branch(name=name, is_active=True))

    existing_subjects = set((await session.scalars(select(Subject.name))).all())
    for name in SUBJECTS:
        if name not in existing_subjects:
            session.add(Subject(name=name, is_active=True))

    await session.flush()
    await _merge_it_subjects(session)
    await session.flush()

    branches = list((await session.scalars(select(Branch))).all())
    subjects = list((await session.scalars(select(Subject))).all())
    branches_by_name = {branch.name: branch for branch in branches}
    subjects_by_name = {subject.name: subject for subject in subjects}

    links = set(
        (
            await session.execute(
                select(BranchSubject.branch_id, BranchSubject.subject_id)
            )
        ).all()
    )
    for branch in branches:
        for subject in subjects:
            if not subject.is_active:
                continue
            if (branch.id, subject.id) not in links:
                session.add(BranchSubject(branch_id=branch.id, subject_id=subject.id))

    await _seed_students(session, branches_by_name, subjects_by_name)

    existing_admins = set((await session.scalars(select(Admin.telegram_id))).all())
    for telegram_id in settings.admin_ids:
        if telegram_id not in existing_admins:
            session.add(Admin(telegram_id=telegram_id, full_name=".env administratori"))

    if not await session.scalar(select(Setting).where(Setting.key == "academy_name")):
        session.add(Setting(key="academy_name", value="Al-Aziz Academy"))

    # Birinchi ishga tushishda tanlov avtomatik 7 kunlik qilib yaratiladi.
    # Keyingi qayta ishga tushirishlarda vaqt boshidan boshlanmaydi.
    now = utc_now()
    competition = await session.scalar(
        select(Competition)
        .where(Competition.is_main.is_(True))
        .order_by(Competition.created_at.desc())
    )
    if competition is None:
        competition = await session.scalar(
            select(Competition).order_by(Competition.created_at.desc())
        )

    await session.execute(update(Competition).values(is_main=False))

    if competition is None:
        competition = Competition(
            name="Al-Aziz Academy filiallararo o‘quvchilar tanlovi",
            description="Turli filial o‘quvchilari orasidan eng yaxshisiga ovoz bering!",
            starts_at=now,
            ends_at=now + timedelta(days=7),
            duration_days=7,
            state="active",
            is_main=True,
            notify_start_sent=True,
        )
        session.add(competition)
        await session.flush()
    else:
        competition.name = "Al-Aziz Academy filiallararo o‘quvchilar tanlovi"
        competition.description = (
            "Turli filial o‘quvchilari orasidan eng yaxshisiga ovoz bering!"
        )
        competition.is_main = True
        await session.flush()

    existing_branch_links = set(
        (
            await session.scalars(
                select(CompetitionBranch.branch_id).where(
                    CompetitionBranch.competition_id == competition.id
                )
            )
        ).all()
    )
    for branch in branches:
        if branch.is_active and branch.id not in existing_branch_links:
            session.add(
                CompetitionBranch(
                    competition_id=competition.id,
                    branch_id=branch.id,
                )
            )

    existing_subject_links = set(
        (
            await session.scalars(
                select(CompetitionSubject.subject_id).where(
                    CompetitionSubject.competition_id == competition.id
                )
            )
        ).all()
    )
    for subject in subjects:
        if subject.is_active and subject.id not in existing_subject_links:
            session.add(
                CompetitionSubject(
                    competition_id=competition.id,
                    subject_id=subject.id,
                )
            )

    # Eski 1-4 / 5-11 toifalari qolib ketmasin.
    await session.execute(
        delete(CompetitionCategory).where(
            CompetitionCategory.competition_id == competition.id,
            CompetitionCategory.category.not_in(
                (CATEGORY_PRIMARY, CATEGORY_SECONDARY)
            ),
        )
    )
    existing_categories = set(
        (
            await session.scalars(
                select(CompetitionCategory.category).where(
                    CompetitionCategory.competition_id == competition.id
                )
            )
        ).all()
    )
    for category in (CATEGORY_PRIMARY, CATEGORY_SECONDARY):
        if category not in existing_categories:
            session.add(
                CompetitionCategory(
                    competition_id=competition.id,
                    category=category,
                )
            )

    await session.commit()
