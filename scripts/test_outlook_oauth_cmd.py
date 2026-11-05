"""Parancssoros Outlook OAuth + IMAP teszt (PKCE, böngészős bejelentkezés)."""
from __future__ import annotations

import imaplib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.oauth2_outlook import run_pkce_login  # noqa: E402

DEFAULT_EMAIL = "trosztgergely@outlook.hu"
IMAP_HOST = "outlook.office365.com"
IMAP_PORT = 993


def imap_xoauth2(email: str, access_token: str) -> None:
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=30)
    raw = f"user={email}\1auth=Bearer {access_token}\1\1".encode()
    mail.authenticate("XOAUTH2", lambda _x: raw)
    typ, data = mail.select("INBOX", readonly=True)
    print(f"INBOX select: {typ}, messages hint: {data}")
    mail.logout()


def main() -> int:
    email = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL).strip()
    print(f"E-mail: {email}")
    print("PKCE: megnyílik a Microsoft bejelentkezés…")
    print()

    tok = run_pkce_login(
        email=email,
        on_status=lambda msg: print(msg.replace("\n\n", "\n")),
    )
    if not tok or not tok.get("access_token"):
        print("Nincs token.")
        return 1

    print()
    print("=== IMAP XOAUTH2 teszt ===")
    try:
        imap_xoauth2(email, tok["access_token"])
        print("IMAP OK — bejelentkezés és INBOX olvasás sikerült.")
    except Exception as exc:
        print("IMAP HIBA:", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
