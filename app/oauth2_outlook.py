"""Microsoft Outlook OAuth2 (XOAUTH2 IMAP támogatás)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from app.paths import ROOT


# Microsoft Azure App Registration
# https://portal.azure.com → App registrations → New registration
# Name: Hírlevél Követő
# Redirect URI: http://localhost:8889/callback
CLIENT_ID = "3c1d5b3d-1234-4abc-abcd-abc123def456"  # Szükséges: tényleges ID
CLIENT_SECRET = "your-secret-here"  # Szükséges: titkos kulcs
REDIRECT_URI = "http://localhost:8889/callback"

OAUTH_CACHE = ROOT / "oauth2_outlook.json"


def get_cached_token() -> dict | None:
    """Cachelezett token lekérdezése."""
    if not OAUTH_CACHE.exists():
        return None
    try:
        with open(OAUTH_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_token(token_data: dict) -> None:
    """Token mentése cache-be."""
    try:
        with open(OAUTH_CACHE, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
        # Jogok: csak owner olvashatja (jelszó-like adat)
        OAUTH_CACHE.chmod(0o600)
    except Exception:
        pass


def request_token(email: str) -> dict | None:
    """
    Interactive OAuth2 flow:
    1. Felhasználó böngészőjét megnyitjuk
    2. Microsoft login
    3. Callback: localhost:8889-re
    4. Token lekérdezése
    """
    
    # Ezt csak akkor értelmes, ha van tényleges CLIENT_ID és CLIENT_SECRET
    # (jelenleg placeholder)
    
    auth_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={CLIENT_ID}"
        f"&scope=offline_access%20https://outlook.office365.com/.default"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    )
    
    # Böngésző megnyitása
    print(f"Nyitom a böngészőt: {auth_url}")
    webbrowser.open(auth_url)
    
    # Ideális: HTTP callback szervert indítanánk, de egyszerűbb:
    # Felhasználó kézzel másolja be a callback URL-t
    # Authorization code lekérdezése
    
    callback_url = input(
        "Microsoft login után másolj be a redirect URL-t (localhost:8889/callback?code=...): "
    ).strip()
    
    # Code kinyerése
    if "code=" not in callback_url:
        return None
    
    code = callback_url.split("code=")[1].split("&")[0]
    
    # Token kérés
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "scope": "offline_access https://outlook.office365.com/.default",
    }
    
    try:
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(token_data).encode("utf-8"),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_response = json.loads(resp.read().decode("utf-8"))
            
        if "access_token" in token_response:
            save_token(token_response)
            return token_response
        else:
            print(f"Token hiba: {token_response.get('error_description')}")
            return None
    except Exception as e:
        print(f"Token kérés hiba: {e}")
        return None


def get_access_token(email: str) -> str | None:
    """
    Access token lekérdezése (refresh vagy új).
    Egyelőre: placeholder (prod-ban: refresh token kezelés).
    """
    cached = get_cached_token()
    if cached and "access_token" in cached:
        # TODO: Check expiry, refresh if needed
        return cached["access_token"]
    
    # Nincs cached token → új login
    token = request_token(email)
    if token:
        return token.get("access_token")
    
    return None


def clear_cached_token() -> None:
    """Token törlése (kijelentkezés)."""
    if OAUTH_CACHE.exists():
        try:
            OAUTH_CACHE.unlink()
        except Exception:
            pass
