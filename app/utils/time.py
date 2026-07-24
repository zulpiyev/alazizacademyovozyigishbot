from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Treat SQLite's timezone-naive timestamps as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def local_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def to_local(value: datetime) -> datetime:
    return ensure_utc(value).astimezone(local_timezone())


def parse_local_datetime(value: str) -> datetime:
    local = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M").replace(
        tzinfo=local_timezone()
    )
    return local.astimezone(UTC)


def format_local(value: datetime) -> str:
    return to_local(value).strftime("%d.%m.%Y %H:%M")


def competition_status(
    state: str, starts_at: datetime, ends_at: datetime, now: datetime | None = None
) -> str:
    now = ensure_utc(now or utc_now())
    starts_at = ensure_utc(starts_at)
    ends_at = ensure_utc(ends_at)
    if state == "finished" or now >= ends_at:
        return "finished"
    if state == "paused":
        return "paused"
    if state == "draft" or now < starts_at:
        return "scheduled"
    return "active"


def status_label(status: str) -> str:
    return {
        "draft": "⚪ Qoralama",
        "scheduled": "🟡 Hali boshlanmagan",
        "active": "🟢 Ovoz berish davom etmoqda",
        "paused": "⏸ Vaqtincha to‘xtatilgan",
        "finished": "🔴 Ovoz berish yakunlangan",
    }.get(status, "⚪ Noma’lum")


def remaining_parts(
    ends_at: datetime, now: datetime | None = None
) -> tuple[int, int, int]:
    now = ensure_utc(now or utc_now())
    ends_at = ensure_utc(ends_at)
    seconds = max(0, int((ends_at - now).total_seconds()))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    return days, hours, minutes


def remaining_text(ends_at: datetime, now: datetime | None = None) -> str:
    days, hours, minutes = remaining_parts(ends_at, now)
    if days:
        return f"{days} kun {hours} soat {minutes} daqiqa"
    if hours:
        return f"{hours} soat {minutes} daqiqa"
    return f"{minutes} daqiqa"


def duration_end(starts_at: datetime, days: int) -> datetime:
    return ensure_utc(starts_at) + timedelta(days=days)
