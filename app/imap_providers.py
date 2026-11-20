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
    # password: jelszó / alkalmazásjelszó IMAP; oauth_microsoft: csak Microsoft bejelentkezés
    auth: str = "password"


# Thunderbird-szerű előre kitöltött IMAP profilok
PROVIDERS: list[ImapProvider] = [
    ImapProvider(
        key="gmail",
        label="Gmail",
        host="imap.gmail.com",
        help_url="https://myaccount.google.com/apppasswords",
        hint="Google alkalmazásjelszó kell (2FA után). Nem a szokásos Gmail-jelszó.",
    ),
    ImapProvider(
        key="outlook",
        label="Outlook / Hotmail / Live",
        host="outlook.office365.com",
        help_url="https://account.microsoft.com/security",
        auth="oauth_microsoft",
        hint="Kattints a „Bejelentkezés Microsoft-fiókkal” gombra — a böngészőben jelentkezz be.",
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
        key="vipmail",
        label="Vipmail",
        host="imap.vipmail.hu",
        help_url="https://vipmail.hu/",
        hint="Vipmail fiók jelszava (IMAP).",
    ),
    ImapProvider(
        key="proton_bridge",
        label="ProtonMail — kísérleti (Bridge)",
        host="127.0.0.1",
        port=1143,
        help_url="https://proton.me/mail/bridge",
        hint=(
            "Kísérleti: csak a Proton Mail Bridge programmal működik (telepítés + futás kötelező).\n"
            "IMAP: 127.0.0.1, port 1143 (Bridge alap). Jelszó: a Bridge által generált jelszó "
            "(nem a proton.me webes jelszó).\n"
            "Nincs garancia; a fejlesztő saját Proton-fiókon nem tesztelte — visszajelzés örömmel."
        ),
    ),
    ImapProvider(
        key="custom",
        label="Egyéni / más szolgáltató",
        host="",
        help_url="https://support.mozilla.org/hu/kb/automatic-account-configuration",
        hint=(
            "Add meg a szolgáltató IMAP szerverét (host + port, általában 993).\n"
            "Protonhoz ne ezt válaszd — használd a „ProtonMail — kísérleti (Bridge)” profilt."
        ),
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
    "outlook.hu": "outlook",
    "hotmail.com": "outlook",
    "hotmail.hu": "outlook",
    "live.com": "outlook",
    "live.hu": "outlook",
    "msn.com": "outlook",
    "yahoo.com": "yahoo",
    "yahoo.co.uk": "yahoo",
    "ymail.com": "yahoo",
    "icloud.com": "icloud",
    "me.com": "icloud",
    "mac.com": "icloud",
    "freemail.hu": "freemail",
    "citromail.hu": "citromail",
    "vipmail.hu": "vipmail",
    "proton.me": "proton_bridge",
    "protonmail.com": "proton_bridge",
    "pm.me": "proton_bridge",
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


def provider_uses_microsoft_oauth(provider_key: str) -> bool:
    p = PROVIDERS_BY_KEY.get((provider_key or "").strip().lower())
    return bool(p and p.auth == "oauth_microsoft")


def supported_providers_summary() -> str:
    """Rövid lista súgóhoz / fiókablakhoz."""
    names = [p.label for p in PROVIDERS if p.key != "custom"]
    return ", ".join(names)
