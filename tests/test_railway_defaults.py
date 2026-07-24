from app.config import Settings


def test_default_required_channels_are_alaziz_channels():
    settings = Settings(BOT_TOKEN="123456:TEST_TOKEN")
    channels = settings.required_channels

    assert [channel.chat_id for channel in channels] == [
        "@alaziz_academy",
        "@abdulaziz_avazovichY",
    ]
    assert [channel.url for channel in channels] == [
        "https://t.me/alaziz_academy",
        "https://t.me/abdulaziz_avazovichY",
    ]
