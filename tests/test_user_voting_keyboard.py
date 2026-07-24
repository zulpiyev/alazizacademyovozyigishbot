from types import SimpleNamespace

from app.keyboards.user import categories_kb, students_list_kb, subjects_kb


def test_subjects_are_one_per_row_and_have_no_branch_id():
    subjects = [
        SimpleNamespace(id=1, name="Ingliz tili"),
        SimpleNamespace(id=2, name="Rus tili"),
        SimpleNamespace(id=3, name="Matematika"),
    ]
    markup = subjects_kb(subjects, prefix="vsub", back_callback="main:home")
    subject_rows = markup.inline_keyboard[:3]
    assert all(len(row) == 1 for row in subject_rows)
    assert [row[0].callback_data for row in subject_rows] == [
        "vsub:1",
        "vsub:2",
        "vsub:3",
    ]


def test_student_button_shows_branch_and_casts_vote_directly():
    students = [
        SimpleNamespace(
            id=101,
            full_name="Polonchiyev Polchi",
            branch=SimpleNamespace(name="Olmazor"),
        ),
        SimpleNamespace(
            id=102,
            full_name="Ali Valiyev",
            branch=SimpleNamespace(name="Chinoz"),
        ),
    ]
    markup = students_list_kb(
        students, subject_id=2, category="1-6", page=0, total=2
    )
    student_rows = markup.inline_keyboard[:2]
    assert all(len(row) == 1 for row in student_rows)
    assert [row[0].text for row in student_rows] == [
        "🏫 Olmazor — Polonchiyev Polchi",
        "🏫 Chinoz — Ali Valiyev",
    ]
    assert [row[0].callback_data for row in student_rows] == [
        "vcast:101",
        "vcast:102",
    ]


def test_only_two_grade_groups_are_shown():
    markup = categories_kb(2, "vlist", "main:vote")
    grade_rows = markup.inline_keyboard[:2]
    assert [row[0].text for row in grade_rows] == [
        "📘 1–6-sinflar",
        "📗 7–11-sinflar",
    ]
    assert [row[0].callback_data for row in grade_rows] == [
        "vlist:2:1-6:0",
        "vlist:2:7-11:0",
    ]


def test_student_keyboard_uses_actual_student_count_not_ten():
    students = [
        SimpleNamespace(
            id=index,
            full_name=f"O‘quvchi {index}",
            branch=SimpleNamespace(name="Olmazor"),
        )
        for index in range(1, 14)
    ]
    markup = students_list_kb(
        students, subject_id=1, category="1-6", page=0, total=len(students)
    )
    student_buttons = [
        row[0] for row in markup.inline_keyboard if row and row[0].callback_data.startswith("vcast:")
    ]
    assert len(student_buttons) == 13
