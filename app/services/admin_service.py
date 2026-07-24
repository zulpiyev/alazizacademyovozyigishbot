from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants import CATEGORY_PRIMARY, CATEGORY_SECONDARY
from app.models import Branch, BranchSubject, Student, Subject


def category_for_grade(grade: int) -> str:
    if 0 <= grade <= 6:
        return CATEGORY_PRIMARY
    if 7 <= grade <= 11:
        return CATEGORY_SECONDARY
    raise ValueError("Sinf 0 dan 11 gacha bo‘lishi kerak")


async def list_branches(
    session: AsyncSession, include_inactive: bool = True
) -> list[Branch]:
    stmt = select(Branch).order_by(Branch.name)
    if not include_inactive:
        stmt = stmt.where(Branch.is_active.is_(True))
    return list((await session.scalars(stmt)).all())


async def create_branch(session: AsyncSession, name: str) -> Branch:
    name = name.strip()
    if await session.scalar(
        select(Branch.id).where(func.lower(Branch.name) == name.lower())
    ):
        raise ValueError("Bu filial avval qo‘shilgan")
    branch = Branch(name=name)
    session.add(branch)
    await session.flush()
    subject_ids = (await session.scalars(select(Subject.id))).all()
    session.add_all(
        [
            BranchSubject(branch_id=branch.id, subject_id=subject_id)
            for subject_id in subject_ids
        ]
    )
    await session.commit()
    return branch


async def rename_branch(session: AsyncSession, branch: Branch, name: str) -> None:
    name = name.strip()
    duplicate = await session.scalar(
        select(Branch.id).where(
            func.lower(Branch.name) == name.lower(), Branch.id != branch.id
        )
    )
    if duplicate:
        raise ValueError("Bu nomdagi filial mavjud")
    branch.name = name
    await session.commit()


async def toggle_branch(session: AsyncSession, branch: Branch) -> None:
    branch.is_active = not branch.is_active
    await session.commit()


async def delete_branch(session: AsyncSession, branch: Branch) -> None:
    if await session.scalar(
        select(func.count(Student.id)).where(Student.branch_id == branch.id)
    ):
        raise ValueError(
            "Filialda o‘quvchilar bor. Avval ularni boshqa filialga o‘tkazing."
        )
    await session.delete(branch)
    await session.commit()


async def list_subjects(
    session: AsyncSession, include_inactive: bool = True
) -> list[Subject]:
    stmt = select(Subject).order_by(Subject.name)
    if not include_inactive:
        stmt = stmt.where(Subject.is_active.is_(True))
    return list((await session.scalars(stmt)).all())


async def create_subject(session: AsyncSession, name: str) -> Subject:
    name = name.strip()
    if await session.scalar(
        select(Subject.id).where(func.lower(Subject.name) == name.lower())
    ):
        raise ValueError("Bu fan avval qo‘shilgan")
    subject = Subject(name=name)
    session.add(subject)
    await session.flush()
    branch_ids = (await session.scalars(select(Branch.id))).all()
    session.add_all(
        [BranchSubject(branch_id=i, subject_id=subject.id) for i in branch_ids]
    )
    await session.commit()
    return subject


async def rename_subject(session: AsyncSession, subject: Subject, name: str) -> None:
    name = name.strip()
    duplicate = await session.scalar(
        select(Subject.id).where(
            func.lower(Subject.name) == name.lower(), Subject.id != subject.id
        )
    )
    if duplicate:
        raise ValueError("Bu nomdagi fan mavjud")
    subject.name = name
    await session.commit()


async def toggle_subject(session: AsyncSession, subject: Subject) -> None:
    subject.is_active = not subject.is_active
    await session.commit()


async def delete_subject(session: AsyncSession, subject: Subject) -> None:
    if await session.scalar(
        select(func.count(Student.id)).where(Student.subject_id == subject.id)
    ):
        raise ValueError(
            "Fanga o‘quvchilar biriktirilgan. Avval ularni boshqa fanga o‘tkazing."
        )
    await session.delete(subject)
    await session.commit()


async def toggle_branch_subject(
    session: AsyncSession, branch_id: int, subject_id: int
) -> bool:
    link = await session.scalar(
        select(BranchSubject).where(
            BranchSubject.branch_id == branch_id,
            BranchSubject.subject_id == subject_id,
        )
    )
    if link:
        link.is_active = not link.is_active
        enabled = link.is_active
    else:
        session.add(
            BranchSubject(branch_id=branch_id, subject_id=subject_id, is_active=True)
        )
        enabled = True
    await session.commit()
    return enabled


async def subjects_for_branch(session: AsyncSession, branch_id: int) -> list[Subject]:
    stmt = (
        select(Subject)
        .join(BranchSubject, BranchSubject.subject_id == Subject.id)
        .where(
            BranchSubject.branch_id == branch_id,
            BranchSubject.is_active.is_(True),
            Subject.is_active.is_(True),
        )
        .order_by(Subject.name)
    )
    return list((await session.scalars(stmt)).all())


async def create_student(
    session: AsyncSession,
    first_name: str,
    last_name: str,
    branch_id: int,
    subject_id: int,
    grade: int,
    photo_file_id: str | None = None,
) -> Student:
    category = category_for_grade(grade)
    duplicate = await session.scalar(
        select(Student.id).where(
            func.lower(Student.first_name) == first_name.strip().lower(),
            func.lower(Student.last_name) == last_name.strip().lower(),
            Student.branch_id == branch_id,
            Student.subject_id == subject_id,
            Student.grade == grade,
        )
    )
    if duplicate:
        raise ValueError("Bu o‘quvchi shu filial, fan va sinfda mavjud")
    student = Student(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        branch_id=branch_id,
        subject_id=subject_id,
        grade=grade,
        category=category,
        photo_file_id=photo_file_id,
    )
    session.add(student)
    await session.commit()
    return student


async def get_student(session: AsyncSession, student_id: int) -> Student | None:
    stmt = (
        select(Student)
        .options(selectinload(Student.branch), selectinload(Student.subject))
        .where(Student.id == student_id)
    )
    return await session.scalar(stmt)


async def list_students(
    session: AsyncSession,
    page: int = 0,
    page_size: int = 10,
    branch_id: int | None = None,
    subject_id: int | None = None,
    category: str | None = None,
    include_inactive: bool = True,
) -> tuple[list[Student], int]:
    filters = []
    if branch_id:
        filters.append(Student.branch_id == branch_id)
    if subject_id:
        filters.append(Student.subject_id == subject_id)
    if category:
        filters.append(Student.category == category)
    if not include_inactive:
        filters.append(Student.is_active.is_(True))
    count = await session.scalar(select(func.count(Student.id)).where(*filters)) or 0
    stmt = (
        select(Student)
        .join(Branch, Branch.id == Student.branch_id)
        .options(selectinload(Student.branch), selectinload(Student.subject))
        .where(*filters)
        .order_by(Branch.name, Student.last_name, Student.first_name)
        .offset(page * page_size)
        .limit(page_size)
    )
    return list((await session.scalars(stmt)).all()), count


async def update_student_name(
    session: AsyncSession, student: Student, first_name: str, last_name: str
) -> None:
    student.first_name = first_name.strip()
    student.last_name = last_name.strip()
    await session.commit()


async def update_student_grade(
    session: AsyncSession, student: Student, grade: int
) -> None:
    student.grade = grade
    student.category = category_for_grade(grade)
    await session.commit()


async def update_student_group(
    session: AsyncSession, student: Student, branch_id: int, subject_id: int
) -> None:
    student.branch_id = branch_id
    student.subject_id = subject_id
    await session.commit()


async def update_student_photo(
    session: AsyncSession, student: Student, photo_file_id: str | None
) -> None:
    student.photo_file_id = photo_file_id
    await session.commit()


async def toggle_student(session: AsyncSession, student: Student) -> None:
    student.is_active = not student.is_active
    await session.commit()


async def delete_student(session: AsyncSession, student: Student) -> None:
    await session.delete(student)
    await session.commit()
