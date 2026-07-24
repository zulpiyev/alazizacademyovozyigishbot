from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.keyboards.common import main_menu_kb
from app.utils.competition_text import countdown_text


def test_finished_main_menu_only_has_statistics():
    markup = main_menu_kb(voting_enabled=False)
    buttons = [button for row in markup.inline_keyboard for button in row]
    assert [button.text for button in buttons] == ["📊 Statistika"]
    assert [button.callback_data for button in buttons] == ["main:stats"]


def test_finished_countdown_says_time_is_over():
    now = datetime.now(UTC)
    competition = SimpleNamespace(
        state="active",
        starts_at=now - timedelta(days=8),
        ends_at=now - timedelta(seconds=1),
    )
    text = countdown_text(competition)
    assert "Vaqt tugadi" in text
    assert "faqat statistikani" in text
