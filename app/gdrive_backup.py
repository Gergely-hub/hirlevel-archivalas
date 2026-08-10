"""Google Drive biztonsági mentés (OAuth) — OneDrive/Dropbox később."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Optional

from app.paths import PROJECT_ROOT, ROOT, ensure_data_dir

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = ROOT / "gdrive_token.json"
CREDS_PATH = ROOT / "gdrive_credentials.json"
APP_FOLDER_NAME = "HirlevelKoveto-backup"

# Egyszeri előkészítéshez (böngésző) — AccountChooser: egyértelmű fiókválasztás
def _console_url(path: str) -> str:
    from urllib.parse import quote

    return (
        "https://accounts.google.com/AccountChooser?continue="
        + quote("https://console.cloud.google.com" + path, safe="")
    )


URL_PROJECT = _console_url("/projectcreate")
URL_DRIVE_API = _console_url("/apis/library/drive.googleapis.com")
URL_CONSENT = _console_url("/apis/credentials/consent")
URL_CREDENTIALS = _console_url("/apis/credentials")


def _candidate_credential_files() -> list[Path]:
    """Hol keressük az alkalmazás Google-azonosítóját."""
    ensure_data_dir()
    out: list[Path] = [CREDS_PATH]
    # Exe mellett / projektben (egyszer bemásolva)
    try:
        from app.paths import PROJECT_ROOT as pr

        out.append(pr / "gdrive_credentials.json")
    except Exception:
        pass
    out.append(PROJECT_ROOT / "gdrive_credentials.json")
    # Egyedi nevek a Letöltésekből
    dl = Path.home() / "Downloads"
    if dl.is_dir():
        try:
            for p in sorted(dl.glob("client_secret*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                out.append(p)
        except OSError:
            pass
    return out


def ensure_credentials_installed() -> bool:
    """Ha van JSON máshol, bemásolja AppData-ba. True = elérhető."""
    ensure_data_dir()
    if CREDS_PATH.is_file() and _looks_like_oauth_json(CREDS_PATH):
        return True
    for src in _candidate_credential_files():
        if src.resolve() == CREDS_PATH.resolve():
            continue
        if src.is_file() and _looks_like_oauth_json(src):
            try:
                shutil.copy2(src, CREDS_PATH)
                return True
            except OSError:
                continue
    return CREDS_PATH.is_file() and _looks_like_oauth_json(CREDS_PATH)


def _looks_like_oauth_json(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return False
    block = data.get("installed") or data.get("web") or {}
    return bool(block.get("client_id") and block.get("client_secret"))


def install_credentials_from_file(src: Path | str) -> Path:
    """Letöltött Google JSON bemásolása a program adatkönyvtárába."""
    ensure_data_dir()
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(str(src))
    if not _looks_like_oauth_json(src):
        raise ValueError(
            "Ez nem megfelelő Google-azonosító fájl.\n"
            "A Google Console-ból az „Asztali alkalmazás” JSON-t válaszd."
        )
    shutil.copy2(src, CREDS_PATH)
    return CREDS_PATH


def credentials_available() -> bool:
    return ensure_credentials_installed()


def is_connected() -> bool:
    return TOKEN_PATH.is_file() and credentials_available()


def _load_flow():
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not credentials_available():
        raise FileNotFoundError(
            "Még nincs előkészítve a Google Drive.\n"
            "Beállítások → Google Drive előkészítés…"
        )
    return InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)


def _load_creds():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN_PATH.is_file():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def connect_interactive() -> str:
    """Böngészős bejelentkezés a felhasználó saját Google-fiókjával."""
    ensure_data_dir()
    flow = _load_flow()
    creds = flow.run_local_server(port=0, prompt="consent")
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return "Google Drive csatlakoztatva. A mentések a saját Drive-odra kerülnek."


def disconnect() -> None:
    if TOKEN_PATH.exists():
        try:
            TOKEN_PATH.unlink()
        except OSError:
            pass


def _drive_service():
    from googleapiclient.discovery import build

    creds = _load_creds()
    if creds is None or not creds.valid:
        raise RuntimeError(
            "Nincs Google Drive bejelentkezés.\nBeállítások → Google Drive bejelentkezés…"
        )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _ensure_backup_folder(service: Any) -> str:
    q = (
        f"name = '{APP_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    res = (
        service.files()
        .list(q=q, spaces="drive", fields="files(id,name)", pageSize=5)
        .execute()
    )
    files = res.get("files") or []
    if files:
        return str(files[0]["id"])
    meta = {
        "name": APP_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    created = service.files().create(body=meta, fields="id").execute()
    return str(created["id"])


def upload_backup_zip(local_path: Path | str, *, keep: int = 8) -> str:
    from googleapiclient.http import MediaFileUpload

    local_path = Path(local_path)
    if not local_path.is_file():
        raise FileNotFoundError(str(local_path))

    service = _drive_service()
    folder_id = _ensure_backup_folder(service)
    media = MediaFileUpload(str(local_path), mimetype="application/zip", resumable=True)
    meta = {"name": local_path.name, "parents": [folder_id]}
    created = (
        service.files()
        .create(body=meta, media_body=media, fields="id,name")
        .execute()
    )
    _prune_remote(service, folder_id, keep=keep)
    return str(created.get("id") or "")


def _prune_remote(service: Any, folder_id: str, *, keep: int = 8) -> None:
    keep = max(1, int(keep))
    q = f"'{folder_id}' in parents and trashed = false and name contains 'HirlevelKoveto-backup-'"
    res = (
        service.files()
        .list(
            q=q,
            spaces="drive",
            fields="files(id,name,createdTime)",
            orderBy="createdTime desc",
            pageSize=50,
        )
        .execute()
    )
    files = res.get("files") or []
    for f in files[keep:]:
        try:
            service.files().delete(fileId=f["id"]).execute()
        except Exception:
            pass


def status_text() -> str:
    if not credentials_available():
        return "Nincs előkészítve (Beállítások → Google Drive előkészítés)"
    if is_connected():
        return "Google Drive: bejelentkezve"
    return "Google Drive: nincs bejelentkezés"
