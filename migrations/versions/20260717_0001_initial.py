"""Initial production schema.

Revision ID: 20260717_0001
Revises: None
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("language_code", sa.String(16)),
        sa.Column(
            "is_blocked", sa.Boolean(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("telegram_id", name="uq_admins_telegram_id"),
    )
    op.create_index("ix_admins_telegram_id", "admins", ["telegram_id"])

    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_branches_name"),
    )
    op.create_index("ix_branches_name", "branches", ["name"])

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_subjects_name"),
    )
    op.create_index("ix_subjects_name", "subjects", ["name"])

    op.create_table(
        "branch_subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_id",
            sa.Integer(),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            sa.Integer(),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("branch_id", "subject_id", name="uq_branch_subject"),
    )
    op.create_index("ix_branch_subjects_branch_id", "branch_subjects", ["branch_id"])
    op.create_index("ix_branch_subjects_subject_id", "branch_subjects", ["subject_id"])

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column(
            "branch_id",
            sa.Integer(),
            sa.ForeignKey("branches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            sa.Integer(),
            sa.ForeignKey("subjects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("grade", sa.SmallInteger(), nullable=False),
        sa.Column("category", sa.String(10), nullable=False),
        sa.Column("photo_file_id", sa.String(512)),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("grade BETWEEN 0 AND 11", name="ck_students_grade"),
        sa.CheckConstraint("category IN ('1-6', '7-11')", name="ck_students_category"),
    )
    op.create_index("ix_students_branch_id", "students", ["branch_id"])
    op.create_index("ix_students_subject_id", "students", ["subject_id"])
    op.create_index("ix_students_category", "students", ["category"])
    op.create_index(
        "ix_students_group",
        "students",
        ["branch_id", "subject_id", "category", "is_active"],
    )

    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_days", sa.Integer(), server_default="7", nullable=False),
        sa.Column("state", sa.String(20), server_default="scheduled", nullable=False),
        sa.Column(
            "is_main", sa.Boolean(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("paused_at", sa.DateTime(timezone=True)),
        sa.Column(
            "notify_start_sent",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "notify_3d_sent",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "notify_1d_sent",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "notify_1h_sent",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "notify_end_sent",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("duration_days > 0", name="ck_competitions_duration"),
    )
    op.create_index("ix_competitions_starts_at", "competitions", ["starts_at"])
    op.create_index("ix_competitions_ends_at", "competitions", ["ends_at"])
    op.create_index("ix_competitions_is_main", "competitions", ["is_main"])
    op.create_index("ix_competitions_main_state", "competitions", ["is_main", "state"])
    op.create_index(
        "uq_competitions_single_main",
        "competitions",
        ["is_main"],
        unique=True,
        sqlite_where=sa.text("is_main = 1"),
    )

    op.create_table(
        "competition_branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            sa.Integer(),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "competition_id", "branch_id", name="uq_competition_branch"
        ),
    )
    op.create_index(
        "ix_competition_branches_competition_id",
        "competition_branches",
        ["competition_id"],
    )
    op.create_index(
        "ix_competition_branches_branch_id", "competition_branches", ["branch_id"]
    )

    op.create_table(
        "competition_subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            sa.Integer(),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "competition_id", "subject_id", name="uq_competition_subject"
        ),
    )
    op.create_index(
        "ix_competition_subjects_competition_id",
        "competition_subjects",
        ["competition_id"],
    )
    op.create_index(
        "ix_competition_subjects_subject_id", "competition_subjects", ["subject_id"]
    )

    op.create_table(
        "competition_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(10), nullable=False),
        sa.UniqueConstraint(
            "competition_id", "category", name="uq_competition_category"
        ),
    )
    op.create_index(
        "ix_competition_categories_competition_id",
        "competition_categories",
        ["competition_id"],
    )

    op.create_table(
        "votes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            sa.Integer(),
            sa.ForeignKey("branches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            sa.Integer(),
            sa.ForeignKey("subjects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("category", sa.String(10), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("voter_full_name", sa.String(255), nullable=False),
        sa.Column(
            "voted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "telegram_id",
            "competition_id",
            "subject_id",
            "category",
            name="uq_vote_user_subject_category",
        ),
    )
    op.create_index("ix_votes_user_id", "votes", ["user_id"])
    op.create_index("ix_votes_telegram_id", "votes", ["telegram_id"])
    op.create_index("ix_votes_student_id", "votes", ["student_id"])
    op.create_index("ix_votes_competition_id", "votes", ["competition_id"])
    op.create_index("ix_votes_branch_id", "votes", ["branch_id"])
    op.create_index("ix_votes_subject_id", "votes", ["subject_id"])
    op.create_index("ix_votes_category", "votes", ["category"])
    op.create_index(
        "ix_votes_group",
        "votes",
        ["competition_id", "subject_id", "category", "student_id"],
    )
    op.create_index("ix_votes_time", "votes", ["voted_at"])

    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("message_type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("telegram_file_id", sa.String(512)),
        sa.Column("sent_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(30), server_default="completed", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(150), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("key", name="uq_settings_key"),
    )
    op.create_index("ix_settings_key", "settings", ["key"])


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("broadcasts")
    op.drop_table("votes")
    op.drop_table("competition_categories")
    op.drop_table("competition_subjects")
    op.drop_table("competition_branches")
    op.drop_table("competitions")
    op.drop_table("students")
    op.drop_table("branch_subjects")
    op.drop_table("subjects")
    op.drop_table("branches")
    op.drop_table("admins")
    op.drop_table("users")
