from datetime import UTC, datetime, timedelta

from app.services.admin_service import category_for_grade
from app.utils.time import competition_status, remaining_parts


def test_grade_categories() -> None:
    assert category_for_grade(0) == "1-6"
    assert category_for_grade(1) == "1-6"
    assert category_for_grade(6) == "1-6"
    assert category_for_grade(7) == "7-11"
    assert category_for_grade(11) == "7-11"


def test_competition_status() -> None:
    now = datetime.now(UTC)
    assert (
        competition_status(
            "scheduled", now + timedelta(hours=1), now + timedelta(days=1), now
        )
        == "scheduled"
    )
    assert (
        competition_status(
            "active", now - timedelta(hours=1), now + timedelta(hours=1), now
        )
        == "active"
    )
    assert (
        competition_status(
            "paused", now - timedelta(hours=1), now + timedelta(hours=1), now
        )
        == "paused"
    )
    assert (
        competition_status(
            "active", now - timedelta(days=2), now - timedelta(seconds=1), now
        )
        == "finished"
    )


def test_remaining_parts() -> None:
    now = datetime.now(UTC)
    days, hours, minutes = remaining_parts(
        now + timedelta(days=2, hours=3, minutes=4), now
    )
    assert (days, hours, minutes) == (2, 3, 4)
