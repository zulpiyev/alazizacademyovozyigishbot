from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import ROOT_DIR, get_settings


def setup_logging() -> None:
    settings = get_settings()
    log_dir = ROOT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_dir / "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        handlers=[file_handler, stream_handler],
        force=True,
    )
