"""Microsoft Outlook OAuth2 — eszközkód (device code), IMAP XOAUTH2."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from typing import Any

from app.db import load_config, save_config

# Delegált IMAP (Outlook.com / Microsoft 365)
IMAP_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access openid email profile"

TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
DEVICE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"


def microsoft_client_id() -> str:
    cfg = load_config()
    cid = str(cfg.get("microsoft_oauth_client_id") or "").strip()
    return cid


def set_microsoft_client_id(client_id: str) -> None:
    cfg = load_config()
    cfg["microsoft_oauth_client_id"] = client_id.strip()
    save_config(cfg)


def start_device_flow(client_id: str) -> dict[str, Any]:
    body = urllib.parse.urlencode(
        {"client_id": client_id, "scope": IMAP_SCOPE}
    ).encode("utf-8")
    req = urllib.request.Request(DEVICE_URL, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_device_tokens(client_id: str, device_code: str) -> dict[str, Any]:
    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id,
            "device_code": device_code,
        }
    ).encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def refresh_access_token(client_id: str, refresh_token: str) -> dict[str, Any]:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
            "scope": IMAP_SCOPE,
        }
    ).encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_device_login(
    *,
    on_status: Any = None,
    timeout_sec: int = 600,
) -> dict[str, Any] | None:
    """
    Eszközkódos Microsoft bejelentkezés (2FA a microsoft.com oldalon).
    Vissza: access_token, refresh_token, expires_in — vagy None.
    """
    client_id = microsoft_client_id()
    if not client_id:
        raise ValueError(
            "Hiányzik a Microsoft OAuth alkalmazás-ID (Azure). "
            "Add meg a Levelező fiókok ablakban, vagy a config.json "
            "microsoft_oauth_client_id mezőjében."
        )

    def status(msg: str) -> None:
        if on_status:
            on_status(msg)

    status("Eszközkód kérése…")
    dev = start_device_flow(client_id)
    user_code = dev.get("user_code") or ""
    uri = dev.get("verification_uri") or "https://microsoft.com/devicelogin"
    message = dev.get("message") or f"Nyisd meg {uri} és add meg: {user_code}"
    device_code = dev.get("device_code") or ""
    interval = int(dev.get("interval") or 5)
    expires = int(dev.get("expires_in") or 900)

    status(f"{message}")
    try:
        webbrowser.open(uri)
    except Exception:
        pass

    deadline = time.monotonic() + min(timeout_sec, expires)
    while time.monotonic() < deadline:
        time.sleep(max(3, interval))
        try:
            tok = poll_device_tokens(client_id, device_code)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            try:
                err = json.loads(err_body)
            except json.JSONDecodeError:
                err = {"error": err_body}
            code = str(err.get("error") or "")
            if code in ("authorization_pending", "slow_down"):
                status("Várakozás a Microsoft bejelentkezésre…")
                continue
            if code == "expired_token":
                status("Lejárt az eszközkód — indítsd újra.")
                return None
            raise ValueError(err.get("error_description") or err_body) from exc

        if tok.get("access_token"):
            status("Microsoft bejelentkezés sikeres.")
            return tok
        status("Várakozás…")

    status("Időtúllépés — nem érkezett bejelentkezés.")
    return None


def try_refresh_account_tokens(
    oauth_refresh_token: str | None,
) -> dict[str, str] | None:
    """Refresh token → új access (+ esetleg refresh). None ha nem sikerült."""
    if not oauth_refresh_token:
        return None
    client_id = microsoft_client_id()
    if not client_id:
        return None
    try:
        tok = refresh_access_token(client_id, oauth_refresh_token)
    except Exception:
        return None
    if not tok.get("access_token"):
        return None
    return {
        "oauth_token": str(tok["access_token"]),
        "oauth_refresh_token": str(tok.get("refresh_token") or oauth_refresh_token),
    }
