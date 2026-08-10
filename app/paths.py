from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _project_root() -> Path:
    """Fejlesztés: repo gyökér. .exe: az exe mappája."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _user_data_root() -> Path:
    """Közös hely Python és exe indításnál — ne legyen több DB."""
    return Path.home() / "AppData" / "Local" / "HirlevelKoveto"


ROOT = _user_data_root()
PROJECT_ROOT = _project_root()
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "hirlevelek.db"
CONFIG_PATH = ROOT / "config.json"

_example_candidates = [
    PROJECT_ROOT / "config.example.json",
    _bundle_dir() / "config.example.json",
    ROOT / "config.example.json",
]
CONFIG_EXAMPLE = next((p for p in _example_candidates if p.exists()), PROJECT_ROOT / "config.example.json")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_files()


def _migrate_legacy_files() -> None:
    """Régi helyekről áthozza a configot / DB-t, ha az új hely még üres."""
    candidates_cfg = [
        PROJECT_ROOT / "config.json",
        PROJECT_ROOT / "release" / "HirlevelKoveto" / "config.json",
        PROJECT_ROOT / "dist" / "HirlevelKoveto" / "config.json",
    ]
    if not CONFIG_PATH.exists():
        for src in candidates_cfg:
            if src.exists():
                try:
                    shutil.copy2(src, CONFIG_PATH)
                    break
                except OSError:
                    pass

    candidates_db = [
        PROJECT_ROOT / "data" / "hirlevelek.db",
        PROJECT_ROOT / "release" / "HirlevelKoveto" / "data" / "hirlevelek.db",
        PROJECT_ROOT / "dist" / "HirlevelKoveto" / "data" / "hirlevelek.db",
    ]
    if not DB_PATH.exists():
        best: Path | None = None
        best_size = -1
        for src in candidates_db:
            if src.exists() and src.stat().st_size > best_size:
                # csak ha van messages tábla / nem üres sémájú
                best = src
                best_size = src.stat().st_size
        if best and best_size > 10_000:
            try:
                shutil.copy2(best, DB_PATH)
            except OSError:
                pass
