from __future__ import annotations


def subscription_required_text(
    channel_count: int = 2, check_failed: bool = False
) -> str:
    count_text = f"{channel_count} ta" if channel_count else "majburiy"
    text = (
        "🔒 <b>Ovoz berishdan oldin kanallarga obuna bo‘ling</b>\n\n"
        f"Quyidagi {count_text} kanalga obuna bo‘ling, so‘ng "
        "<b>✅ Obunani tekshirish</b> tugmasini bosing.\n\n"
        "Barcha kanallarga obuna bo‘lmaguncha ovoz berish ochilmaydi."
    )
    if check_failed:
        text += (
            "\n\n⚠️ Obunani tekshirishda xato bo‘ldi. "
            "Bot barcha kanallarda administrator ekanini tekshiring."
        )
    return text
