from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.database.base import Base

settings = get_settings()

engine_options: dict[str, object] = {"pool_pre_ping": True}
if settings.is_sqlite:
    engine_options["connect_args"] = {"timeout": 30}
else:
    engine_options.update({"pool_size": 10, "max_overflow": 20})

engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    **engine_options,
)

if settings.is_sqlite:

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


def _parse_sqlite_datetime(value):
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.now(timezone.utc)
    text_value = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text_value)
    except ValueError:
        return datetime.now(timezone.utc)


def _category_for_grade(grade: int) -> str:
    return "1-6" if int(grade) <= 6 else "7-11"


def _read_vote_rows(connection: Connection) -> list[dict[str, object]]:
    inspector = inspect(connection)
    if "votes" not in inspector.get_table_names():
        return []

    columns = {column["name"] for column in inspector.get_columns("votes")}
    category_expr = "v.category" if "category" in columns else "s.category"
    rows = connection.execute(
        text(
            f"""
            SELECT
                v.id,
                v.user_id,
                v.telegram_id,
                v.student_id,
                v.competition_id,
                v.branch_id,
                v.subject_id,
                {category_expr} AS old_category,
                s.grade AS student_grade,
                v.username,
                v.voter_full_name,
                v.voted_at
            FROM votes AS v
            LEFT JOIN students AS s ON s.id = v.student_id
            ORDER BY v.id
            """
        )
    ).mappings().all()

    deduplicated: list[dict[str, object]] = []
    seen: set[tuple[int, int, int, str]] = set()
    for row in rows:
        if row["student_grade"] is not None:
            category = _category_for_grade(int(row["student_grade"]))
        elif row["old_category"] in {"1-6", "1-4"}:
            category = "1-6"
        else:
            category = "7-11"

        key = (
            int(row["telegram_id"]),
            int(row["competition_id"]),
            int(row["subject_id"]),
            category,
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "telegram_id": row["telegram_id"],
                "student_id": row["student_id"],
                "competition_id": row["competition_id"],
                "branch_id": row["branch_id"],
                "subject_id": row["subject_id"],
                "category": category,
                "username": row["username"],
                "voter_full_name": row["voter_full_name"],
                "voted_at": _parse_sqlite_datetime(row["voted_at"]),
            }
        )
    return deduplicated


def _upgrade_sqlite_category_schema(connection: Connection) -> None:
    """Eski 1-4/5-11 bazani 1-6/7-11 tizimiga xavfsiz o‘tkazadi."""
    from app.models import Student, Vote

    inspector = inspect(connection)
    if "students" not in inspector.get_table_names():
        return

    students_sql = connection.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='students'")
    ).scalar_one_or_none() or ""
    votes_sql = connection.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='votes'")
    ).scalar_one_or_none() or ""

    students_need_rebuild = (
        "'1-4'" in students_sql
        or "'5-11'" in students_sql
        or "BETWEEN 1 AND 11" in students_sql
    )
    votes_need_rebuild = (
        students_need_rebuild
        or "uq_vote_user_subject_category" not in votes_sql
        or "1-4" in votes_sql
        or "5-11" in votes_sql
    )

    vote_rows = _read_vote_rows(connection) if votes_need_rebuild else []

    if students_need_rebuild:
        student_rows = connection.execute(
            text(
                """
                SELECT id, first_name, last_name, branch_id, subject_id, grade,
                       photo_file_id, is_active, created_at, updated_at
                FROM students
                ORDER BY id
                """
            )
        ).mappings().all()

        if "votes" in inspector.get_table_names():
            connection.execute(text("DROP TABLE votes"))
        connection.execute(text("DROP TABLE students"))

        Student.__table__.create(connection, checkfirst=False)
        converted_students = [
            {
                "id": row["id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "branch_id": row["branch_id"],
                "subject_id": row["subject_id"],
                "grade": row["grade"],
                "category": _category_for_grade(int(row["grade"])),
                "photo_file_id": row["photo_file_id"],
                "is_active": row["is_active"],
                "created_at": _parse_sqlite_datetime(row["created_at"]),
                "updated_at": _parse_sqlite_datetime(row["updated_at"]),
            }
            for row in student_rows
        ]
        if converted_students:
            connection.execute(Student.__table__.insert(), converted_students)

        Vote.__table__.create(connection, checkfirst=False)
        if vote_rows:
            connection.execute(Vote.__table__.insert(), vote_rows)
    elif votes_need_rebuild:
        if "votes" in inspector.get_table_names():
            connection.execute(text("DROP TABLE votes"))
        Vote.__table__.create(connection, checkfirst=False)
        if vote_rows:
            connection.execute(Vote.__table__.insert(), vote_rows)

    if "competition_categories" in inspect(connection).get_table_names():
        connection.execute(
            text(
                "DELETE FROM competition_categories "
                "WHERE category IN ('1-4', '5-11')"
            )
        )
        connection.execute(
            text(
                "INSERT OR IGNORE INTO competition_categories "
                "(competition_id, category) "
                "SELECT id, '1-6' FROM competitions"
            )
        )
        connection.execute(
            text(
                "INSERT OR IGNORE INTO competition_categories "
                "(competition_id, category) "
                "SELECT id, '7-11' FROM competitions"
            )
        )


def _upgrade_postgresql_category_schema(connection: Connection) -> None:
    """PostgreSQL bazadagi eski 1-4/5-11 toifalarni yangilaydi."""
    inspector = inspect(connection)
    if "students" not in inspector.get_table_names():
        return

    checks = inspector.get_check_constraints("students")
    old_schema = any(
        "1-4" in str(item.get("sqltext", ""))
        or "5-11" in str(item.get("sqltext", ""))
        or "BETWEEN 1 AND 11" in str(item.get("sqltext", ""))
        for item in checks
    )
    if not old_schema:
        return

    # Toifalar o‘zgarganda 5-6-sinflardagi eski ovozlar 1-6 guruhiga
    # ko‘chadi. Vaqtincha unique constraint olib tashlanib, takrorlar
    # birinchi ovozni saqlagan holda tozalanadi.
    connection.execute(
        text(
            "ALTER TABLE votes "
            "DROP CONSTRAINT IF EXISTS uq_vote_user_subject_category"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE students "
            "DROP CONSTRAINT IF EXISTS ck_students_category"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE students "
            "DROP CONSTRAINT IF EXISTS ck_students_grade"
        )
    )
    connection.execute(
        text(
            "UPDATE students SET category = "
            "CASE WHEN grade <= 6 THEN '1-6' ELSE '7-11' END"
        )
    )
    connection.execute(
        text(
            "UPDATE votes AS v SET category = "
            "CASE WHEN s.grade <= 6 THEN '1-6' ELSE '7-11' END "
            "FROM students AS s WHERE s.id = v.student_id"
        )
    )
    connection.execute(
        text(
            "DELETE FROM votes AS newer USING votes AS older "
            "WHERE newer.id > older.id "
            "AND newer.telegram_id = older.telegram_id "
            "AND newer.competition_id = older.competition_id "
            "AND newer.subject_id = older.subject_id "
            "AND newer.category = older.category"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE votes ADD CONSTRAINT uq_vote_user_subject_category "
            "UNIQUE (telegram_id, competition_id, subject_id, category)"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE students ADD CONSTRAINT ck_students_grade "
            "CHECK (grade BETWEEN 0 AND 11)"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE students ADD CONSTRAINT ck_students_category "
            "CHECK (category IN ('1-6', '7-11'))"
        )
    )

    connection.execute(
        text(
            "DELETE FROM competition_categories "
            "WHERE category IN ('1-4', '5-11')"
        )
    )
    connection.execute(
        text(
            "INSERT INTO competition_categories (competition_id, category) "
            "SELECT id, '1-6' FROM competitions ON CONFLICT DO NOTHING"
        )
    )
    connection.execute(
        text(
            "INSERT INTO competition_categories (competition_id, category) "
            "SELECT id, '7-11' FROM competitions ON CONFLICT DO NOTHING"
        )
    )


async def initialize_database() -> None:
    # Import models so SQLAlchemy knows every table before create_all().
    import app.models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if settings.is_sqlite:
            await connection.run_sync(_upgrade_sqlite_category_schema)
        elif connection.dialect.name == "postgresql":
            await connection.run_sync(_upgrade_postgresql_category_schema)
