from __future__ import annotations


def subscription_required_text(
    channel_count: int = 2, check_failed: bool = False
) -> str:
    count_text = f"{channel_count} ta" if channel_count else "majburiy"
    text = (
        "🔒 <b>Ovoz berishdan oldin sahifalarga obuna bo‘ling</b>\n\n"
        f"Quyidagi {count_text} Telegram kanalga obuna bo‘ling va "
        "Instagram sahifamizni kuzatib qo‘ying. So‘ng "
        "<b>✅ Obunani tekshirish</b> tugmasini bosing."
    )
    if check_failed:
        text += "\n\n⚠️ <b>Oldin kanallarga obuna bo‘ling.</b>"
    return text
