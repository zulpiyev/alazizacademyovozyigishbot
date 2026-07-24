from types import SimpleNamespace

from aiogram.enums import ChatMemberStatus

from app.config import Settings
from app.keyboards.common import subscription_kb
from app.services.subscription_service import _is_member


def test_required_channels_are_parsed_from_settings():
    settings = Settings(
        BOT_TOKEN="123456:TEST_TOKEN",
        REQUIRED_CHANNEL_1_ID="@kanal_bir",
        REQUIRED_CHANNEL_1_NAME="Kanal bir",
        REQUIRED_CHANNEL_1_URL="",
        REQUIRED_CHANNEL_2_ID="-1001234567890",
        REQUIRED_CHANNEL_2_NAME="Kanal ikki",
        REQUIRED_CHANNEL_2_URL="https://t.me/+invite",
    )
    channels = settings.required_channels
    assert len(channels) == 2
    assert channels[0].chat_id == "@kanal_bir"
    assert channels[0].url == "https://t.me/kanal_bir"
    assert channels[1].chat_id == -1001234567890


def test_subscription_keyboard_has_two_channels_and_check_button():
    settings = Settings(
        BOT_TOKEN="123456:TEST_TOKEN",
        REQUIRED_CHANNEL_1_ID="@kanal_bir",
        REQUIRED_CHANNEL_1_NAME="Kanal bir",
        REQUIRED_CHANNEL_2_ID="@kanal_ikki",
        REQUIRED_CHANNEL_2_NAME="Kanal ikki",
    )
    markup = subscription_kb(settings.required_channels)
    assert len(markup.inline_keyboard) == 3
    assert markup.inline_keyboard[0][0].url == "https://t.me/kanal_bir"
    assert markup.inline_keyboard[1][0].url == "https://t.me/kanal_ikki"
    assert markup.inline_keyboard[2][0].callback_data == "subscription:check"


def test_member_statuses_are_accepted():
    assert _is_member(SimpleNamespace(status=ChatMemberStatus.MEMBER))
    assert _is_member(SimpleNamespace(status=ChatMemberStatus.ADMINISTRATOR))
    assert _is_member(SimpleNamespace(status=ChatMemberStatus.CREATOR))
    assert _is_member(
        SimpleNamespace(status=ChatMemberStatus.RESTRICTED, is_member=True)
    )
    assert not _is_member(SimpleNamespace(status=ChatMemberStatus.LEFT))
    assert not _is_member(SimpleNamespace(status=ChatMemberStatus.KICKED))
