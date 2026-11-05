"""Helyi biztonsági mentés / visszaállítás (zip) — gépre."""

from __future__ import annotations

import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from app.paths import CONFIG_PATH, DB_PATH, ensure_data_dir


BACKUP_DB_NAME = "hirlevelek.db"
BACKUP_CONFIG_NAME = "config.json"
BACKUP_META_NAME = "backup_meta.txt"
BACKUP_PREFIX = "HirlevelKoveto-backup-"
BACKUP_KEEP_DEFAULT = 8

def default_backup_filename() -> str:
    return f"{BACKUP_PREFIX}{datetime.now():%Y%m%d-%H%M}.zip"


def create_backup_zip(dest: Path | str) -> Path:
    """Konzisztens SQLite másolat + config → zip. Visszaadja a zip útvonalát."""
    ensure_data_dir()
    dest = Path(dest)
    if dest.suffix.lower() != ".zip":
        dest = dest.with_suffix(".zip")
    dest.parent.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Nincs adatbázis: {DB_PATH}")

    tmp_db = dest.with_suffix(".db.tmp")
    try:
        src = sqlite3.connect(str(DB_PATH), timeout=30.0)
        try:
            src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass
        dst = sqlite3.connect(str(tmp_db))
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
        src.close()

        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_db, arcname=BACKUP_DB_NAME)
            if CONFIG_PATH.exists():
                zf.write(CONFIG_PATH, arcname=BACKUP_CONFIG_NAME)
            zf.writestr(
                BACKUP_META_NAME,
                (
                    f"HirlevelKoveto backup\n"
                    f"created={datetime.now().isoformat(timespec='seconds')}\n"
                    f"db={DB_PATH}\n"
                    "Megjegyzés: a config.json tartalmazhatja a levelező jelszavakat.\n"
                ),
            )
    finally:
        if tmp_db.exists():
            try:
                tmp_db.unlink()
            except OSError:
                pass

    return dest


def list_backup_zips(folder: Path | str) -> list[Path]:
    folder = Path(folder)
    if not folder.is_dir():
        return []
    files = [
        p
        for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() == ".zip"
        and p.name.startswith(BACKUP_PREFIX)
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def prune_old_backups(folder: Path | str, keep: int = BACKUP_KEEP_DEFAULT) -> int:
    """Törli a legrégebbi saját backup zip-eket. Vissza: törölt darabszám."""
    keep = max(1, int(keep))
    files = list_backup_zips(folder)
    removed = 0
    for path in files[keep:]:
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def restore_backup_zip(zip_path: Path | str) -> None:
    """Felülírja a helyi DB-t (és configot, ha a zipben van)."""
    ensure_data_dir()
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(str(zip_path))

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        if BACKUP_DB_NAME not in names:
            raise ValueError("Érvénytelen backup: hiányzik a hirlevelek.db")

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for path in (DB_PATH, Path(str(DB_PATH) + "-wal"), Path(str(DB_PATH) + "-shm")):
            if path.exists():
                bak = path.with_name(path.name + f".pre-restore-{stamp}")
                path.replace(bak)

        raw = zf.read(BACKUP_DB_NAME)
        DB_PATH.write_bytes(raw)

        if BACKUP_CONFIG_NAME in names:
            if CONFIG_PATH.exists():
                CONFIG_PATH.replace(
                    CONFIG_PATH.with_name(f"config.json.pre-restore-{stamp}")
                )
            CONFIG_PATH.write_bytes(zf.read(BACKUP_CONFIG_NAME))
