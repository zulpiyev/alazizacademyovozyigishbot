from __future__ import annotations


def subscription_required_text(
    channel_count: int = 2, check_failed: bool = False
) -> str:
    count_text = f"{channel_count} ta" if channel_count else "majburiy"
    text = (
        "🔒 <b>Ovoz berishdan oldin sahifalarga obuna bo‘ling</b>\n\n"
        f"Quyidagi {count_text} Telegram kanalga obuna bo‘ling va "
        "Instagram sahifamizni kuzatib qo‘ying. So‘ng "
        "<b>✅ Obunani tekshirish</b> tugmasini bosing.\n\n"
        "Telegram kanallarga obuna bo‘lmaguncha ovoz berish ochilmaydi.\n"
        "ℹ️ Instagram obunasi oddiy havola orqali ochiladi va avtomatik tekshirilmaydi."
    )
    if check_failed:
        text += (
            "\n\n⚠️ Obunani tekshirishda xato bo‘ldi. "
            "Bot barcha kanallarda administrator ekanini tekshiring."
        )
    return text
