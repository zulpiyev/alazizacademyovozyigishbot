from __future__ import annotations

# Telegram text messages are limited to 4096 characters. We keep some margin
# for HTML tags and future text changes.
MAX_CHUNK_LENGTH = 3800


def split_result_text(
    header_lines: list[str],
    result_blocks: list[str],
    footer_lines: list[str],
) -> list[str]:
    """Split a complete result list into Telegram-safe message chunks.

    Every result block stays intact, so a student's name, vote count and
    percentage are never separated across two messages.
    """
    chunks: list[str] = []
    current = "\n".join(header_lines).strip()

    for block in result_blocks:
        candidate = f"{current}\n{block}" if current else block
        if len(candidate) <= MAX_CHUNK_LENGTH:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = block

    footer = "\n".join(footer_lines).strip()
    if footer:
        candidate = f"{current}\n{footer}" if current else footer
        if len(candidate) <= MAX_CHUNK_LENGTH:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = footer

    if current:
        chunks.append(current)
    return chunks or ["Natijalar mavjud emas."]
