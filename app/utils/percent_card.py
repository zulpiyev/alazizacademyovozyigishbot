from __future__ import annotations

from html import escape


def percent_card_row(
    full_name: str,
    branch_name: str,
    percent: float,
    *,
    selected: bool = False,
) -> str:
    """Return one compact Telegram HTML row for the percentage card."""
    marker = "✅ " if selected else ""
    return (
        f"│ {marker}🏫 <b>{escape(branch_name)}</b> — "
        f"{escape(full_name)} — 📈 <b>{percent:.1f}%</b>"
    )
