from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError

from app.config import RequiredChannel

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubscriptionCheck:
    subscribed: bool
    missing_channels: tuple[RequiredChannel, ...]
    check_failed: bool = False


def _is_member(chat_member) -> bool:
    status = chat_member.status
    if status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
    }:
        return True
    if status == ChatMemberStatus.RESTRICTED:
        return bool(getattr(chat_member, "is_member", False))
    return False


async def check_required_subscriptions(
    bot: Bot,
    user_id: int,
    channels: tuple[RequiredChannel, ...],
) -> SubscriptionCheck:
    """Foydalanuvchining barcha majburiy kanallardagi a'zoligini tekshiradi."""
    if not channels:
        return SubscriptionCheck(subscribed=True, missing_channels=())

    missing: list[RequiredChannel] = []
    check_failed = False

    for channel in channels:
        try:
            member = await bot.get_chat_member(
                chat_id=channel.chat_id,
                user_id=user_id,
            )
        except (TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError) as exc:
            logger.warning(
                "Kanal obunasini tekshirib bo'lmadi: channel=%s user=%s error=%s",
                channel.chat_id,
                user_id,
                exc,
            )
            missing.append(channel)
            check_failed = True
            continue

        if not _is_member(member):
            missing.append(channel)

    return SubscriptionCheck(
        subscribed=not missing,
        missing_channels=tuple(missing),
        check_failed=check_failed,
    )
