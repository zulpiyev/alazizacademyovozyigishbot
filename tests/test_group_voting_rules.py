from collections import Counter

from app.data.default_students import DEFAULT_STUDENTS
from app.models import Vote


def test_real_roster_covers_both_categories():
    counts = Counter(
        (subject, "1-6" if grade <= 6 else "7-11")
        for _name, _branch, subject, grade in DEFAULT_STUDENTS
    )
    assert DEFAULT_STUDENTS
    assert all(count > 0 for count in counts.values())
    assert len(DEFAULT_STUDENTS) == 129
    assert {category for _subject, category in counts} == {"1-6", "7-11"}


def test_vote_unique_rule_is_per_subject_and_category():
    unique_constraints = [
        constraint
        for constraint in Vote.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    ]
    column_sets = [{column.name for column in item.columns} for item in unique_constraints]
    assert {
        "telegram_id",
        "competition_id",
        "subject_id",
        "category",
    } in column_sets
