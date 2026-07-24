from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.config import RequiredChannel
from app.handlers.user import start as start_module
from app.services.subscription_service import SubscriptionCheck


async def test_subscription_check_shows_alert_when_user_is_not_subscribed(monkeypatch):
    channel = RequiredChannel(
        chat_id="@kanal",
        name="Kanal",
        url="https://t.me/kanal",
    )
    settings = SimpleNamespace(
        required_channels=(channel,),
        instagram_name="Instagram — @alazizacademy",
        instagram_url="https://www.instagram.com/alazizacademy/",
    )
    callback = MagicMock()
    callback.from_user = SimpleNamespace(id=123)
    callback.bot = MagicMock()
    session = MagicMock()

    monkeypatch.setattr(start_module, "get_settings", lambda: settings)
    monkeypatch.setattr(start_module, "upsert_user", AsyncMock())
    monkeypatch.setattr(
        start_module,
        "check_required_subscriptions",
        AsyncMock(
            return_value=SubscriptionCheck(
                subscribed=False,
                missing_channels=(channel,),
                check_failed=True,
            )
        ),
    )
    edit_mock = AsyncMock()
    answer_mock = AsyncMock()
    monkeypatch.setattr(start_module, "edit_or_send", edit_mock)
    monkeypatch.setattr(start_module, "answer_callback", answer_mock)

    await start_module.subscription_check_handler(callback, session)

    edit_mock.assert_awaited_once()
    answer_mock.assert_awaited_once_with(
        callback, "⚠️ Oldin kanallarga obuna bo‘ling.", True
    )


async def test_subscription_check_opens_menu_and_confirms_when_subscribed(monkeypatch):
    channel = RequiredChannel(
        chat_id="@kanal",
        name="Kanal",
        url="https://t.me/kanal",
    )
    settings = SimpleNamespace(
        required_channels=(channel,),
        instagram_name="Instagram — @alazizacademy",
        instagram_url="https://www.instagram.com/alazizacademy/",
    )
    callback = MagicMock()
    callback.from_user = SimpleNamespace(id=456)
    callback.bot = MagicMock()
    session = MagicMock()

    monkeypatch.setattr(start_module, "get_settings", lambda: settings)
    monkeypatch.setattr(start_module, "upsert_user", AsyncMock())
    monkeypatch.setattr(
        start_module,
        "check_required_subscriptions",
        AsyncMock(
            return_value=SubscriptionCheck(
                subscribed=True,
                missing_channels=(),
                check_failed=False,
            )
        ),
    )
    start_mock = AsyncMock(return_value=("MENU", MagicMock()))
    edit_mock = AsyncMock()
    answer_mock = AsyncMock()
    monkeypatch.setattr(start_module, "_start_text_and_keyboard", start_mock)
    monkeypatch.setattr(start_module, "edit_or_send", edit_mock)
    monkeypatch.setattr(start_module, "answer_callback", answer_mock)

    await start_module.subscription_check_handler(callback, session)

    start_mock.assert_awaited_once_with(
        session,
        456,
        callback.bot,
        skip_subscription_check=True,
    )
    answer_mock.assert_awaited_once_with(callback, "✅ Obuna tasdiqlandi!")
