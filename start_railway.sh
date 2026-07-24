#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1
DATA_DIR="${RAILWAY_VOLUME_MOUNT_PATH:-/app/data}"
mkdir -p "$DATA_DIR"

# Railway Variables ichida DATABASE_URL berilmasa, SQLite bazani
# ulangan Volume ichida saqlaydi.
if [[ -z "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="sqlite+aiosqlite:///${DATA_DIR}/alaziz_voting.db"
fi

echo "Al-Aziz Voting Bot Railway'da ishga tushmoqda..."
echo "Database location: ${DATA_DIR}/alaziz_voting.db"
exec python bot.py
