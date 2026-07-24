from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))
    is_blocked: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )


class Branch(Base, TimestampMixin):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )

    students: Mapped[list[Student]] = relationship(back_populates="branch")
    subject_links: Mapped[list[BranchSubject]] = relationship(
        back_populates="branch", cascade="all, delete-orphan"
    )


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )

    students: Mapped[list[Student]] = relationship(back_populates="subject")
    branch_links: Mapped[list[BranchSubject]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )


class BranchSubject(Base, TimestampMixin):
    __tablename__ = "branch_subjects"
    __table_args__ = (
        UniqueConstraint("branch_id", "subject_id", name="uq_branch_subject"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )

    branch: Mapped[Branch] = relationship(back_populates="subject_links")
    subject: Mapped[Subject] = relationship(back_populates="branch_links")


class Student(Base, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("grade BETWEEN 0 AND 11", name="ck_students_grade"),
        CheckConstraint("category IN ('1-6', '7-11')", name="ck_students_category"),
        Index("ix_students_group", "branch_id", "subject_id", "category", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), index=True
    )
    grade: Mapped[int] = mapped_column(SmallInteger)
    category: Mapped[str] = mapped_column(String(10), index=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )

    branch: Mapped[Branch] = relationship(back_populates="students")
    subject: Mapped[Subject] = relationship(back_populates="students")
    votes: Mapped[list[Vote]] = relationship(back_populates="student")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Competition(Base, TimestampMixin):
    __tablename__ = "competitions"
    __table_args__ = (
        CheckConstraint("duration_days > 0", name="ck_competitions_duration"),
        Index("ix_competitions_main_state", "is_main", "state"),
        Index(
            "uq_competitions_single_main",
            "is_main",
            unique=True,
            sqlite_where=text("is_main = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_days: Mapped[int] = mapped_column(Integer, default=7, server_default="7")
    state: Mapped[str] = mapped_column(
        String(20), default="scheduled", server_default="scheduled"
    )
    is_main: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", index=True
    )
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notify_start_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    notify_3d_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    notify_1d_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    notify_1h_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    notify_end_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )

    branch_links: Mapped[list[CompetitionBranch]] = relationship(
        back_populates="competition", cascade="all, delete-orphan"
    )
    subject_links: Mapped[list[CompetitionSubject]] = relationship(
        back_populates="competition", cascade="all, delete-orphan"
    )
    category_links: Mapped[list[CompetitionCategory]] = relationship(
        back_populates="competition", cascade="all, delete-orphan"
    )


class CompetitionBranch(Base):
    __tablename__ = "competition_branches"
    __table_args__ = (
        UniqueConstraint("competition_id", "branch_id", name="uq_competition_branch"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), index=True
    )

    competition: Mapped[Competition] = relationship(back_populates="branch_links")


class CompetitionSubject(Base):
    __tablename__ = "competition_subjects"
    __table_args__ = (
        UniqueConstraint("competition_id", "subject_id", name="uq_competition_subject"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True
    )

    competition: Mapped[Competition] = relationship(back_populates="subject_links")


class CompetitionCategory(Base):
    __tablename__ = "competition_categories"
    __table_args__ = (
        UniqueConstraint("competition_id", "category", name="uq_competition_category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(10))

    competition: Mapped[Competition] = relationship(back_populates="category_links")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint(
            "telegram_id",
            "competition_id",
            "subject_id",
            "category",
            name="uq_vote_user_subject_category",
        ),
        Index(
            "ix_votes_group",
            "competition_id",
            "subject_id",
            "category",
            "student_id",
        ),
        Index("ix_votes_time", "voted_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), index=True
    )
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), index=True
    )
    category: Mapped[str] = mapped_column(String(10), index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    voter_full_name: Mapped[str] = mapped_column(String(255))
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student: Mapped[Student] = relationship(back_populates="votes")


class Broadcast(Base, TimestampMixin):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger)
    message_type: Mapped[str] = mapped_column(String(30))
    content: Mapped[str | None] = mapped_column(Text)
    telegram_file_id: Mapped[str | None] = mapped_column(String(512))
    sent_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(30), default="completed", server_default="completed"
    )


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
