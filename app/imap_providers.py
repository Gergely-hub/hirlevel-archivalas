from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ImapProvider:
    key: str
    label: str
    host: str
    port: int = 993
    help_url: str = ""
    hint: str = ""


# Thunderbird-szerű előre kitöltött IMAP profilok
PROVIDERS: list[ImapProvider] = [
    ImapProvider(
        key="gmail",
        label="Gmail",
        host="imap.gmail.com",
        help_url="https://myaccount.google.com/apppasswords",
        hint="Google alkalmazásjelszó kell (2FA után).",
    ),
    ImapProvider(
        key="outlook",
        label="Outlook / Hotmail / Live",
        host="outlook.office365.com",
        help_url="https://account.microsoft.com/security",
        hint="Microsoft fióknál gyakran alkalmazásjelszó vagy IMAP engedély kell.",
    ),
    ImapProvider(
        key="yahoo",
        label="Yahoo Mail",
        host="imap.mail.yahoo.com",
        help_url="https://login.yahoo.com/account/security",
        hint="Yahoo alkalmazásjelszó kell.",
    ),
    ImapProvider(
        key="icloud",
        label="iCloud Mail",
        host="imap.mail.me.com",
        help_url="https://appleid.apple.com/account/manage",
        hint="Apple azonosító → alkalmazás-specifikus jelszó.",
    ),
    ImapProvider(
        key="freemail",
        label="Freemail",
        host="imap.freemail.hu",
        help_url="https://freemail.hu/",
        hint="Freemail jelszó / IMAP hozzáférés.",
    ),
    ImapProvider(
        key="citromail",
        label="Citromail",
        host="imap.citromail.hu",
        help_url="https://citromail.hu/",
        hint="Citromail fiók jelszava.",
    ),
    ImapProvider(
        key="custom",
        label="Egyéni IMAP (mint Thunderbird)",
        host="",
        hint="Add meg a szolgáltató IMAP szerverét (host + port).",
    ),
]

PROVIDERS_BY_KEY = {p.key: p for p in PROVIDERS}
PROVIDER_LABELS = [p.label for p in PROVIDERS]
LABEL_TO_KEY = {p.label: p.key for p in PROVIDERS}

# Domain → provider tipp az e-mailből
_DOMAIN_HINTS: dict[str, str] = {
    "gmail.com": "gmail",
    "googlemail.com": "gmail",
    "outlook.com": "outlook",
    "hotmail.com": "outlook",
    "live.com": "outlook",
    "msn.com": "outlook",
    "yahoo.com": "yahoo",
    "yahoo.co.uk": "yahoo",
    "ymail.com": "yahoo",
    "icloud.com": "icloud",
    "me.com": "icloud",
    "mac.com": "icloud",
    "freemail.hu": "freemail",
    "citromail.hu": "citromail",
}


def guess_provider_key(email: str) -> str:
    domain = (email or "").rsplit("@", 1)[-1].strip().lower()
    return _DOMAIN_HINTS.get(domain, "custom")


def resolve_imap(
    provider_key: str,
    *,
    imap_host: str = "",
    imap_port: int | str | None = None,
) -> tuple[str, int]:
    """Visszaadja a (host, port) párt — üres hostnál Gmail fallback a régi confighoz."""
    key = (provider_key or "gmail").strip().lower()
    preset = PROVIDERS_BY_KEY.get(key)
    host = (imap_host or "").strip()
    port = 993
    if imap_port not in (None, ""):
        try:
            port = int(imap_port)
        except (TypeError, ValueError):
            port = 993

    if key == "custom":
        if not host:
            host = "imap.gmail.com"
        return host, port if port else 993

    if preset and preset.host:
        return preset.host, preset.port

    if host:
        return host, port if port else 993
    return "imap.gmail.com", 993


def provider_label(key: str) -> str:
    p = PROVIDERS_BY_KEY.get((key or "").lower())
    return p.label if p else "Egyéni IMAP"
