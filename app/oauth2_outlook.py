"""Microsoft Outlook OAuth2 — PKCE (böngészős bejelentkezés), IMAP XOAUTH2."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.db import load_config, save_config

# MSAL: csak az IMAP scope — openid / offline_access / profile reserved (MSAL adja).
MSAL_INTERACTIVE_SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]
# Token refresh (urllib): offline_access kell a refresh tokenhez.
IMAP_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"

# Mozilla Thunderbird nyilvános desktop client ID (PKCE / loopback, mint a levelezőkliens).
# Felülírható: config.json → microsoft_oauth_client_id
DEFAULT_MICROSOFT_OAUTH_CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"


def _authority(email: str = "") -> str:
    """Személyes Outlook (@outlook.*, hotmail, live) → consumers; egyébként common."""
    dom = (email.split("@")[-1] if "@" in email else "").lower()
    if dom in (
        "outlook.com",
        "outlook.hu",
        "hotmail.com",
        "hotmail.hu",
        "live.com",
        "live.hu",
        "msn.com",
    ):
        return "consumers"
    return "common"


def _authority_url(email: str = "") -> str:
    return f"https://login.microsoftonline.com/{_authority(email)}"


def _token_url(email: str = "") -> str:
    return f"{_authority_url(email)}/oauth2/v2.0/token"


def microsoft_client_id() -> str:
    cfg = load_config()
    cid = str(cfg.get("microsoft_oauth_client_id") or "").strip()
    return cid or DEFAULT_MICROSOFT_OAUTH_CLIENT_ID


def set_microsoft_client_id(client_id: str) -> None:
    cfg = load_config()
    cfg["microsoft_oauth_client_id"] = client_id.strip()
    save_config(cfg)


def refresh_access_token(
    client_id: str, refresh_token: str, email: str = ""
) -> dict[str, Any]:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
            "scope": IMAP_SCOPE,
        }
    ).encode("utf-8")
    req = urllib.request.Request(_token_url(email), data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def run_pkce_login(
    *,
    email: str = "",
    on_status: Any = None,
    timeout_sec: int = 300,
) -> dict[str, Any] | None:
    """
    Böngészős Microsoft bejelentkezés (authorization code + PKCE, loopback).
    Vissza: access_token, refresh_token, … — vagy None / kivétel.
    """
    import msal

    client_id = microsoft_client_id()
    authority = _authority_url(email)

    def status(msg: str) -> None:
        if on_status:
            on_status(msg)

    status(
        "Megnyílik a Microsoft bejelentkezés a böngészőben.\n\n"
        "Jelentkezz be ugyanazzal az e-mail címmel, mint az űrlapon."
    )
    app = msal.PublicClientApplication(client_id, authority=authority)
    result = app.acquire_token_interactive(
        scopes=MSAL_INTERACTIVE_SCOPES,
        login_hint=email or None,
        prompt="select_account",
        timeout=timeout_sec,
    )
    if not result:
        status("Bejelentkezés megszakítva.")
        return None
    if "access_token" not in result:
        err = result.get("error_description") or result.get("error") or str(result)
        raise ValueError(err)
    status("Microsoft bejelentkezés sikeres.")
    return result


# Régi név / device code teszthez
run_device_login = run_pkce_login


def try_refresh_account_tokens(
    oauth_refresh_token: str | None,
    email: str = "",
) -> dict[str, str] | None:
    """Refresh token → új access (+ esetleg refresh). None ha nem sikerült."""
    if not oauth_refresh_token:
        return None
    client_id = microsoft_client_id()
    if not client_id:
        return None
    try:
        tok = refresh_access_token(client_id, oauth_refresh_token, email=email)
    except Exception:
        return None
    if not tok.get("access_token"):
        return None
    return {
        "oauth_token": str(tok["access_token"]),
        "oauth_refresh_token": str(tok.get("refresh_token") or oauth_refresh_token),
    }
