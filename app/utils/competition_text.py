from __future__ import annotations

from typing import Protocol

from app.utils.time import competition_status, format_local, remaining_text


class CompetitionLike(Protocol):
    state: str
    starts_at: object
    ends_at: object


def countdown_text(competition: CompetitionLike) -> str:
    """Return a compact competition time banner for user-facing screens."""
    status = competition_status(
        competition.state, competition.starts_at, competition.ends_at
    )
    if status == "active":
        return (
            f"⏳ <b>Qolgan vaqt:</b> {remaining_text(competition.ends_at)}\n"
            f"🏁 <b>Tugash vaqti:</b> {format_local(competition.ends_at)}"
        )
    if status == "scheduled":
        return f"🕐 <b>Boshlanish vaqti:</b> {format_local(competition.starts_at)}"
    if status == "paused":
        return "⏸ <b>Tanlov vaqtincha to‘xtatilgan.</b>"
    return "⏰ <b>Vaqt tugadi!</b>\n📊 Endi faqat statistikani ko‘rish mumkin."


def step_text(title: str, competition: CompetitionLike, details: str | None = None) -> str:
    parts = [title]
    if details:
        parts.extend([details])
    parts.extend(["", countdown_text(competition)])
    return "\n".join(parts)
