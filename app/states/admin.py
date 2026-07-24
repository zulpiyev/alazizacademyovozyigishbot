from aiogram.fsm.state import State, StatesGroup


class BranchForm(StatesGroup):
    name = State()
    rename = State()


class SubjectForm(StatesGroup):
    name = State()
    rename = State()


class StudentAdd(StatesGroup):
    first_name = State()
    last_name = State()
    branch = State()
    subject = State()
    grade = State()


class StudentEdit(StatesGroup):
    rename = State()
    grade = State()
    move_branch = State()
    move_subject = State()


class CompetitionAdd(StatesGroup):
    name = State()
    description = State()
    starts_at = State()
    duration = State()


class ExcelImport(StatesGroup):
    file = State()


class BroadcastForm(StatesGroup):
    message = State()
