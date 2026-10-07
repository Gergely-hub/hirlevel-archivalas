"""Szinkron debug napló — minden IMAP lépés fájlba (AppData\\Local\\HirlevelKoveto\\data)."""
from __future__ import annotations

from datetime import datetime

from app.paths import DATA_DIR, ensure_data_dir

LOG_PATH = DATA_DIR / "sync_debug.log"
_MAX_BYTES = 2_500_000


def log(msg: str) -> None:
    ensure_data_dir()
    line = f"{datetime.now().isoformat(timespec='seconds')}  {msg}\n"
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > _MAX_BYTES:
            old = LOG_PATH.read_text(encoding="utf-8", errors="replace")
            LOG_PATH.write_text(old[len(old) // 2 :], encoding="utf-8")
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def session_banner(kind: str, **extra: object) -> None:
    parts = " ".join(f"{k}={v!r}" for k, v in extra.items())
    log(f"======== {kind} ========{(' ' + parts) if parts else ''}")


def log_path_str() -> str:
    return str(LOG_PATH)
