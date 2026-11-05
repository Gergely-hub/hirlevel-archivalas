from __future__ import annotations

import email
import html as html_lib
import imaplib
import re
import time
from datetime import datetime
from email.header import decode_header, make_header
from email.message import Message as EmailMessage
from email.utils import parsedate_to_datetime
from typing import Callable

from bs4 import BeautifulSoup

from app import sync_debug
from app.db import (
    Account,
    Source,
    get_accounts,
    get_message,
    get_source,
    insert_messages_bulk,
    known_gmail_uids,
    list_message_bodies,
    list_sources,
    load_config,
    update_message_body,
)

ProgressCb = Callable[[str], None]


def _emit(progress: ProgressCb | None, msg: str) -> None:
    sync_debug.log(msg)
    if progress:
        progress(msg)


def _oauth_access_token(acc: Account) -> str | None:
    if acc.auth_method != "oauth2":
        return None
    from app.oauth2_outlook import try_refresh_account_tokens

    if acc.oauth_refresh_token:
        ref = try_refresh_account_tokens(acc.oauth_refresh_token, email=acc.email)
        if ref:
            from app.db import update_account_oauth_tokens

            update_account_oauth_tokens(
                acc.email,
                ref["oauth_token"],
                ref.get("oauth_refresh_token"),
            )
            return ref["oauth_token"]
    tok = (acc.oauth_token or "").strip()
    return tok or None


def _imap_login(mail: imaplib.IMAP4_SSL, acc: Account, progress: ProgressCb | None) -> None:
    if acc.auth_method == "oauth2":
        token = _oauth_access_token(acc)
        if not token:
            raise imaplib.IMAP4.error(
                "OAuth2: nincs token — Levelező fiókok → Microsoft OAuth bejelentkezés"
            )
        _emit(progress, f"🔑 OAuth2 (XOAUTH2): {acc.email}")
        # imaplib maga base64-kódolja a callback választ — ne adjunk előre kódolt stringet.
        raw = f"user={acc.email}\1auth=Bearer {token}\1\1".encode()
        mail.authenticate("XOAUTH2", lambda _x: raw)
        return
    _emit(progress, f"🔑 Jelszó login: {acc.email}")
    mail.login(acc.email, acc.app_password)


def test_imap_connection(acc: Account) -> tuple[bool, str]:
    """Thunderbird-szerű teszt: SSL + IMAP bejelentkezés (nincs levélletöltés)."""
    host = (acc.imap_host or "").strip()
    port = int(acc.imap_port or 993)
    try:
        mail = imaplib.IMAP4_SSL(host, port, timeout=30)
        _imap_login(mail, acc, None)
        try:
            mail.logout()
        except Exception:
            pass
        return (
            True,
            f"Sikeresen biztonságos kapcsolatot hozott létre a következővel: {host}:{port}.",
        )
    except Exception as exc:
        return False, _login_error_message(acc, exc)


def _login_error_message(acc: Account, exc: BaseException) -> str:
    raw = str(exc)
    low = raw.lower()
    if "basic authentication is disabled" in low:
        return (
            f"{acc.label}: Outlook nem enged sima jelszót (Basic auth tiltva). "
            "Válaszd az OAuth2 módot → Microsoft OAuth bejelentkezés."
        )
    return f"{acc.label}: bejelentkezés sikertelen — {raw[:120]}"


def _decode_header_value(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def _extract_addr(from_header: str) -> str:
    m = re.search(r"<([^>]+)>", from_header or "")
    if m:
        return m.group(1).strip().lower()
    return (from_header or "").strip().lower()


def _search_uids_for_sender(
    mail: imaplib.IMAP4_SSL,
    sender_email: str,
    *,
    context: str = "",
) -> tuple[list[bytes], str]:
    """FROM keresés — Outlooknál gyakran csak HEADER FROM működik."""
    addr = (sender_email or "").strip().lower()
    if not addr or "@" not in addr:
        return [], ""

    criteria_list = [
        f'(FROM "{addr}")',
        f'(HEADER FROM "{addr}")',
        f'(OR FROM "{addr}" HEADER FROM "{addr}")',
    ]
    domain = addr.split("@", 1)[1]
    if domain:
        criteria_list.append(f'(HEADER FROM "@{domain}")')

    for criteria in criteria_list:
        try:
            typ, data = mail.search(None, criteria)
            if typ == "OK" and data and data[0]:
                uids = data[0].split()
                if uids:
                    sync_debug.log(
                        f"SEARCH OK {context}: {criteria} → {len(uids)} UID"
                    )
                    return uids, criteria
            sync_debug.log(f"SEARCH 0 {context}: {criteria} typ={typ!r}")
        except Exception as exc:
            sync_debug.log(f"SEARCH err {context}: {criteria} → {exc}")

    return [], ""


def _log_recent_inbox_senders(
    mail: imaplib.IMAP4_SSL,
    acc_label: str,
    *,
    want: str,
    limit: int = 10,
) -> None:
    """0 találatnál: naplózza az aktuális mappa utolsó levelei From mezőit (INBOX)."""
    try:
        typ, data = mail.search(None, "ALL")
        if typ != "OK" or not data or not data[0]:
            sync_debug.log(f"{acc_label}: INBOX üres (diagnosztika)")
            return
        uids = data[0].split()[-limit:]
        sync_debug.log(
            f"{acc_label}: 0 találat FOR {want!r} — INBOX utolsó {len(uids)} levél From mezői:"
        )
        for raw_uid in uids:
            typ, msg_data = mail.fetch(
                raw_uid,
                "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])",
            )
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            raw_hdr = msg_data[0][1]
            if not isinstance(raw_hdr, (bytes, bytearray)):
                continue
            hdr = email.message_from_bytes(raw_hdr)
            frm = _decode_header_value(hdr.get("From"))
            subj = _decode_header_value(hdr.get("Subject"))[:60]
            sync_debug.log(f"  uid={_uid_key(raw_uid)} From={frm!r} Subj={subj!r}")
    except Exception as exc:
        sync_debug.log(f"{acc_label}: diagnosztika hiba: {exc}")


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _sanitize_html(html: str) -> str:
    """Olvasópanelhez: script/iframe ki, on* események le."""
    if not (html or "").strip():
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "iframe", "object", "embed", "meta", "link"]):
        tag.decompose()
    for tag in soup.find_all(True):
        attrs = list(tag.attrs.keys())
        for attr in attrs:
            if attr.lower().startswith("on"):
                del tag.attrs[attr]
    body = soup.body
    if body is not None:
        inner = "".join(str(c) for c in body.contents)
        return (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:16px;line-height:1.45;}"
            "img{max-width:100%;height:auto;}a{color:#2563eb;}</style></head><body>"
            f"{inner}</body></html>"
        )
    return str(soup)


def _is_html_fallback_plain(plain: str) -> bool:
    """Hírlevelek plain része gyakran csak 'HTML-t nem tudok megjeleníténi' stub.

    MailerLite stb. stubja ~600–800 karakter (szöveg + hosszú URL) — azt is
    stubnak kell nézni. A hosszú, valós tartalom láblécében lévő „view in browser”
    viszont NEM indokol újratöltést.
    """
    t = (plain or "").strip().lower()
    if not t:
        return True
    hard = (
        "your email software can't display",
        "email software can't display html",
        "can't display html emails",
        "cannot display html emails",
        "can't display html",
        "cannot display html",
        "unable to display html",
        "view newsletter by clicking",
        "view the newsletter by clicking",
    )
    if any(m in t for m in hard):
        return len(t) < 1500
    if len(t) > 450:
        return False
    markers = (
        "can't display this email",
        "html emails",
        "view this email in your browser",
        "view it in your browser",
        "open this email in your browser",
        "ha nem jelenik meg",
        "nem jeleníthető meg",
        "böngészőben tekintsd",
        "bongeszoben tekintsd",
        "having trouble viewing",
    )
    if any(m in t for m in markers):
        return True
    if len(t) < 280 and ("http://" in t or "https://" in t) and t.count("\n") <= 6:
        if "html" in t or "browser" in t or "newsletter" in t or "email" in t:
            return True
    return False


def _is_stub_message(body_text: str, body_html: str) -> bool:
    """Üres/gyenge HTML + stub plain → nincs megjeleníthető hírlevél."""
    html = (body_html or "").strip()
    text = body_text or ""
    if len(html) > 400 and ("<table" in html.lower() or "<div" in html.lower()):
        if not _is_html_fallback_plain(text):
            return False
        # HTML van, de a plain stub — ha a HTML is csak <pre> escaped stub
        if "<pre" in html.lower() and _is_html_fallback_plain(text):
            return True
        return False
    if len(html) < 80:
        return _is_html_fallback_plain(text) or len(text.strip()) < 40
    return _is_html_fallback_plain(text) and len(html) < 400


def _resolve_known_uid(
    account_id: str,
    *,
    message_id: str,
    folder: str,
    imap_uid: str,
    known: set[str],
) -> tuple[str, bool]:
    """DB-beli gmail_uid + ismert-e. Régi fo:123 és új fo:<Message-ID> is."""
    candidates: list[str] = []
    mid = (message_id or "").strip()
    if mid:
        candidates.append(f"{account_id}:{mid}")
    if imap_uid:
        candidates.append(f"{account_id}:{imap_uid}")
        if folder:
            candidates.append(f"{account_id}:{folder}:{imap_uid}")
    for key in candidates:
        if key in known:
            return key, True
    if imap_uid:
        suf = f":{imap_uid}"
        bare = f"{account_id}:{imap_uid}"
        for k in known:
            if k == bare or k.endswith(suf):
                return k, True
    new_key = f"{account_id}:{mid}" if mid else f"{account_id}:{folder}:{imap_uid}"
    return new_key, False


def _imap_quote(value: str) -> str:
    """IMAP SEARCH string — idézőjel és backslash escape."""
    return (value or "").replace("\\", "\\\\").replace('"', '\\"')


def _uids_needing_html_refresh(account_id: str) -> set[str]:
    """Hiányzó / stub HTML-ű levelek."""
    need: set[str] = set()
    for uid, text, html in list_message_bodies(account_id):
        if _is_stub_message(text, html):
            need.add(uid)
    return need


def _parts_from_message(msg: EmailMessage) -> tuple[str, str]:
    """Visszaad: (body_text, body_html)."""
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp.lower():
                continue
            try:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
            except Exception:
                continue
            if ctype == "text/plain":
                plain_parts.append(text)
            elif ctype == "text/html":
                html_parts.append(text)
    else:
        try:
            payload = msg.get_payload(decode=True) or b""
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
        except Exception:
            text = str(msg.get_payload() or "")
        if msg.get_content_type() == "text/html":
            html_parts.append(text)
        else:
            plain_parts.append(text)

    plain = "\n\n".join(p.strip() for p in plain_parts if p.strip())
    raw_html = "\n".join(html_parts) if html_parts else ""
    html_text = _html_to_text(raw_html) if raw_html else ""
    safe_html = _sanitize_html(raw_html) if raw_html else ""

    if html_text:
        if not plain or _is_html_fallback_plain(plain):
            plain = html_text
        elif len(html_text) > len(plain) * 2 and len(plain) < 400:
            plain = html_text

    if not safe_html and plain:
        safe_html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"
            f"<pre style='white-space:pre-wrap;font-family:Segoe UI,Arial,sans-serif'>"
            f"{html_lib.escape(plain)}</pre></body></html>"
        )
    return plain, safe_html


def _body_from_message(msg: EmailMessage) -> str:
    text, _html = _parts_from_message(msg)
    return text


def _list_mailboxes(mail: imaplib.IMAP4_SSL) -> list[str]:
    typ, data = mail.list()
    if typ != "OK" or not data:
        return ["INBOX"]
    names: list[str] = []
    for raw in data:
        line = raw.decode(errors="replace") if isinstance(raw, bytes) else str(raw)
        m = re.search(r' "([^"]+)"$', line) or re.search(r" ([^\s]+)$", line)
        if m:
            names.append(m.group(1))
    return names or ["INBOX"]


def _folder_kind(name: str) -> str:
    cl = (name or "").lower().replace("\\", "/")
    if "trash" in cl or "bin" in cl or "kuka" in cl or "deleted" in cl or "törölt" in cl or "torolt" in cl:
        return "trash"
    if "all mail" in cl or "összes levél" in cl or "osszes level" in cl or "all_mail" in cl:
        return "all"
    if cl == "inbox" or cl.endswith("/inbox") or cl.endswith(".inbox"):
        return "inbox"
    return "other"


def _pick_folders(mail: imaplib.IMAP4_SSL, *, full_import: bool) -> list[str]:
    """INBOX + Kuka; teljes importnál + Összes levél / All Mail."""
    names = _list_mailboxes(mail)
    chosen: list[str] = []

    def add_name(folder: str) -> None:
        if folder and folder not in chosen:
            chosen.append(folder)

    # INBOX mindig
    inbox = next((n for n in names if _folder_kind(n) == "inbox"), None)
    add_name(inbox or "INBOX")

    # Kuka / Trash — törölt hírlevelek visszanyerése
    for n in names:
        if _folder_kind(n) == "trash":
            add_name(n)

    if full_import:
        for n in names:
            if _folder_kind(n) == "all":
                add_name(n)

    return chosen or ["INBOX"]


def _select_folder(mail: imaplib.IMAP4_SSL, folder: str) -> bool:
    typ, _ = mail.select(f'"{folder}"', readonly=True)
    if typ == "OK":
        return True
    typ, _ = mail.select(folder, readonly=True)
    return typ == "OK"


def _uid_key(raw_uid: bytes | str) -> str:
    return raw_uid.decode() if isinstance(raw_uid, bytes) else str(raw_uid)


def fetch_all_accounts(
    progress: ProgressCb | None = None,
    *,
    full_import: bool = False,
) -> dict[str, int]:
    """Inkrementális szinkron (alap), vagy full_import=True az előzményekhez."""
    cfg = load_config()
    raw_count = len(cfg.get("accounts") or [])
    accounts = get_accounts(cfg)
    sync_debug.session_banner(
        "GLOBÁLIS SZINKRON",
        full_import=full_import,
        fiokok=len(accounts),
        config_ben=raw_count,
    )
    if raw_count > len(accounts):
        sync_debug.log(
            f"Figyelem: config.json-ban {raw_count} fiók, "
            f"de csak {len(accounts)} használható (hiányzó/placeholder jelszó?)."
        )
    if not accounts:
        _emit(progress, "Nincs beállított levelező fiók.")
        return {}

    if full_import:
        max_per = int(cfg.get("import_max_per_source") or 500)
        max_per = max(50, min(max_per, 2000))
    else:
        max_per = int(cfg.get("sync_max_per_source") or 40)
        max_per = max(10, min(max_per, 200))

    sources = list_sources(active_only=True)
    by_email = {s.email.lower(): s for s in sources}
    sync_debug.log(
        f"Hírlevél-források ({len(sources)}): "
        + ", ".join(f"{s.name}<{s.email}>" for s in sources[:40])
        + (" …" if len(sources) > 40 else "")
    )
    for acc in accounts:
        sync_debug.log(f"Fiók betöltve: {acc.label} login={acc.email} host={acc.imap_host}")
    sync_debug.log(f"max_per={max_per} (forrásonként / mappánként legfeljebb ennyi UID)")

    totals: dict[str, int] = {}

    for acc in accounts:
        n = _fetch_one_account(
            acc,
            by_email,
            progress,
            max_per=max_per,
            full_import=full_import,
        )
        totals[acc.id] = n
    return totals


def _fetch_one_account(
    acc: Account,
    by_email: dict,
    progress: ProgressCb | None,
    *,
    max_per: int,
    full_import: bool,
) -> int:
    _emit(progress, f"Kapcsolódás: {acc.email} ({acc.imap_host}) …")

    try:
        _emit(progress, f"🔌 Kapcsolódás: {acc.imap_host}:{acc.imap_port} ({acc.auth_method})")

        mail = imaplib.IMAP4_SSL(acc.imap_host, int(acc.imap_port or 993), timeout=45)
        _imap_login(mail, acc, progress)
        _emit(progress, f"✅ Bejelentkezés OK: {acc.label}")
    except imaplib.IMAP4.error as exc:
        _emit(progress, f"❌ IMAP login hiba ({acc.email}): {str(exc)[:100]}")
        return 0
    except Exception as exc:
        _emit(progress, _login_error_message(acc, exc))
        return 0

    known = known_gmail_uids(acc.id)
    needs_refresh = _uids_needing_html_refresh(acc.id)
    # Könnyű szinkron: több stub javítás (régi fo:UID kulcsok miatt)
    refresh_budget = 120 if full_import else 40
    pending: list[tuple[int, str, str, str, str, str, datetime]] = []
    added = 0
    refreshed = 0
    last_progress = 0.0

    def maybe_progress(msg: str) -> None:
        nonlocal last_progress
        sync_debug.log(msg)
        if not progress:
            return
        now = time.monotonic()
        if now - last_progress < 0.4:
            return
        last_progress = now
        progress(msg)

    try:
        folders = _pick_folders(mail, full_import=full_import)
        sync_debug.log(f"{acc.label}: mappák ({len(folders)}): {', '.join(folders[:12])}")
        for folder in folders:
            if not _select_folder(mail, folder):
                sync_debug.log(f"{acc.label}: mappa nem választható: {folder!r}")
                continue
            maybe_progress(f"{acc.label}: {folder}")
            # Kukában többet nézünk — ott lehetnek a törölt HTML-es példányok
            folder_limit = max_per
            if _folder_kind(folder) == "trash":
                folder_limit = max(max_per, 200 if not full_import else max_per)

            for email_addr, source in by_email.items():
                maybe_progress(f"{acc.label} · {acc.email}: {source.name} @ {folder}")

                ctx = f"{acc.label}/{folder}/{source.name}"
                uid_list, _used = _search_uids_for_sender(
                    mail, email_addr, context=ctx
                )
                if not uid_list:
                    if "INBOX" in folder.upper():
                        _log_recent_inbox_senders(
                            mail, acc.label, want=email_addr, limit=8
                        )
                    continue

                sync_debug.log(
                    f"SEARCH {ctx}: {len(uid_list)} UID (feldolgozás max {folder_limit})"
                )
                uids = uid_list[-folder_limit:]
                for raw_uid in reversed(uids):
                    uid_num = _uid_key(raw_uid)

                    typ, msg_data = mail.fetch(
                        raw_uid,
                        "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])",
                    )
                    if typ != "OK" or not msg_data or not msg_data[0]:
                        continue
                    raw_hdr = msg_data[0][1]
                    if not isinstance(raw_hdr, (bytes, bytearray)):
                        continue
                    hdr = email.message_from_bytes(raw_hdr)
                    sender = _extract_addr(_decode_header_value(hdr.get("From")))
                    if sender != email_addr:
                        continue

                    mid = (hdr.get("Message-ID") or "").strip()
                    uid_str, is_known = _resolve_known_uid(
                        acc.id,
                        message_id=mid,
                        folder=folder,
                        imap_uid=uid_num,
                        known=known,
                    )
                    if is_known and uid_str not in needs_refresh:
                        continue
                    if is_known and refreshed >= refresh_budget:
                        # Költségkeret: a többi stub a következő szinkronra marad
                        continue

                    typ, body_data = mail.fetch(raw_uid, "(RFC822)")
                    if typ != "OK" or not body_data or not body_data[0]:
                        continue
                    raw = body_data[0][1]
                    if not isinstance(raw, (bytes, bytearray)):
                        continue
                    msg = email.message_from_bytes(raw)
                    subject = _decode_header_value(msg.get("Subject"))
                    body_text, body_html = _parts_from_message(msg)
                    try:
                        received = parsedate_to_datetime(msg.get("Date"))
                        if received.tzinfo:
                            received = received.astimezone().replace(tzinfo=None)
                    except Exception:
                        received = datetime.now()

                    if is_known:
                        # Stub → valódi HTML (INBOX vagy kuka)
                        if body_html and len(body_html) > 180 and not _is_stub_message(
                            body_text, body_html
                        ):
                            if update_message_body(
                                account_id=acc.id,
                                gmail_uid=uid_str,
                                body_text=body_text,
                                body_html=body_html,
                            ):
                                refreshed += 1
                                needs_refresh.discard(uid_str)
                                maybe_progress(f"{acc.label}: {refreshed} HTML frissítve …")
                        elif body_html and len(body_html) > 180:
                            if update_message_body(
                                account_id=acc.id,
                                gmail_uid=uid_str,
                                body_text=body_text or _html_to_text(body_html),
                                body_html=body_html,
                            ):
                                refreshed += 1
                                needs_refresh.discard(uid_str)
                                maybe_progress(f"{acc.label}: {refreshed} HTML frissítve …")
                        continue

                    pending.append(
                        (source.id, acc.id, uid_str, subject, body_text, body_html, received)
                    )
                    known.add(uid_str)

                    if len(pending) >= 25:
                        added += insert_messages_bulk(pending)
                        pending.clear()
                        maybe_progress(f"{acc.label}: {added} új …")
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    if pending:
        added += insert_messages_bulk(pending)

    if refreshed:
        _emit(
            progress,
            f"{acc.label}: {added} új, {refreshed} HTML frissítve (kuka/INBOX)",
        )
    else:
        _emit(progress, f"{acc.label}: {added} új levél")
    return added + refreshed


def _fetch_one_source_on_account(
    src: Source,
    acc: Account,
    progress: ProgressCb | None,
) -> int:
    """Egy hírlevél-forrás lekérése egy IMAP fiókból (FROM szűrés)."""
    from app.db import known_gmail_uids

    known = known_gmail_uids(acc.id)
    added = 0

    sync_debug.log(
        f"FORRÁS-SZINKRON fiók={acc.label} login={acc.email} "
        f"forrás={src.name} FROM={src.email!r}"
    )
    try:
        mail = imaplib.IMAP4_SSL(acc.imap_host, int(acc.imap_port or 993), timeout=45)
        _imap_login(mail, acc, progress)
        sync_debug.log(f"{acc.label}: bejelentkezés OK")
    except Exception as exc:
        _emit(progress, _login_error_message(acc, exc))
        return 0

    try:
        folders = _pick_folders(mail, full_import=False)
        sync_debug.log(f"{acc.label}: mappák ({len(folders)}): {', '.join(folders[:12])}")
        for folder in folders:
            if not _select_folder(mail, folder):
                sync_debug.log(f"{acc.label}: mappa nem választható: {folder!r}")
                continue

            _emit(progress, f"{acc.label} · {acc.email}: {src.name} @ {folder} …")

            ctx = f"{acc.label}/{folder}/{src.name}"
            uid_list, _used = _search_uids_for_sender(mail, src.email, context=ctx)
            if not uid_list:
                if "INBOX" in folder.upper():
                    _log_recent_inbox_senders(mail, acc.label, want=src.email, limit=8)
                continue

            sync_debug.log(
                f"SEARCH {ctx}: {len(uid_list)} UID (max 40 feldolgozás)"
            )
            uids = uid_list[-40:]
            pending: list[tuple] = []

            for raw_uid in reversed(uids):
                uid_num = _uid_key(raw_uid)

                typ, msg_data = mail.fetch(raw_uid, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0][1]
                if not isinstance(raw, (bytes, bytearray)):
                    continue

                msg = email.message_from_bytes(raw)
                want_from = (src.email or "").strip().lower()
                sender = _extract_addr(_decode_header_value(msg.get("From")))
                if want_from and sender != want_from:
                    continue

                subject = _decode_header_value(msg.get("Subject"))
                body_text, body_html = _parts_from_message(msg)

                try:
                    received = parsedate_to_datetime(msg.get("Date"))
                    if received.tzinfo:
                        received = received.astimezone().replace(tzinfo=None)
                except Exception:
                    received = datetime.now()

                mid = (msg.get("Message-ID") or "").strip()
                uid_str, is_known = _resolve_known_uid(
                    acc.id,
                    message_id=mid,
                    folder=folder,
                    imap_uid=uid_num,
                    known=known,
                )

                if not is_known:
                    pending.append(
                        (src.id, acc.id, uid_str, subject, body_text, body_html, received)
                    )
                    known.add(uid_str)

                if len(pending) >= 10:
                    added += insert_messages_bulk(pending)
                    pending.clear()

            if pending:
                added += insert_messages_bulk(pending)
            sync_debug.log(f"{acc.label}/{folder}: +{added} új eddig (forrás szinkron)")
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    sync_debug.log(f"FORRÁS-SZINKRON vége fiók={acc.label} forrás={src.name} új={added}")
    return added


def fetch_one_source(
    source_id: int,
    progress: ProgressCb | None = None,
) -> int:
    """Egy forrás szinkronizálása — minden beállított fiókban keres (mint a globális szinkron)."""
    from app.db import get_source, get_accounts

    src = get_source(source_id)
    if not src:
        _emit(progress, "Forrás nem található")
        return 0

    sync_debug.session_banner(
        "FORRÁS 🔄",
        forrás=src.name,
        from_email=src.email,
        source_id=src.id,
    )

    cfg = load_config()
    all_accs = get_accounts(cfg)
    if not all_accs:
        _emit(progress, "Nincs beállított levelező fiók.")
        return 0

    # Mindig minden IMAP fiók (nincs rejtett Gmail-kötés a forrásoknál)
    accs = all_accs
    if src.account_id:
        sync_debug.log(
            f"Figyelem: forrás account_id={src.account_id!r} — figyelmen kívül hagyva, "
            f"minden fiókban keresünk."
        )

    for acc in accs:
        sync_debug.log(f"  fiók: {acc.label} ({acc.email}) @ {acc.imap_host}")

    _emit(progress, f"Szinkronizálás: {src.name} ({src.email}) — {len(accs)} fiók …")

    total = 0
    for acc in accs:
        total += _fetch_one_source_on_account(src, acc, progress)

    _emit(progress, f"{src.name}: {total} új levél")
    return total


def refresh_one_message_html(msg_id: int) -> bool:
    """Egy stub levél HTML-jének azonnali letöltése IMAP-ról. True = sikerült."""
    full = get_message(msg_id)
    if not full:
        return False
    if not _is_stub_message(full.body_text or "", full.body_html or ""):
        return False

    cfg = load_config()
    accounts = {a.id: a for a in get_accounts(cfg)}
    acc = accounts.get(full.account_id or "")
    if not acc:
        # account_id nélküli / ismeretlen — első fiók, ha egy van
        accs = list(accounts.values())
        if len(accs) != 1:
            return False
        acc = accs[0]

    src = get_source(full.source_id)
    if not src:
        return False

    # Régi kulcs: fo:2358 → IMAP UID tipp
    imap_uid_hint = ""
    parts = (full.gmail_uid or "").split(":", 1)
    if len(parts) == 2 and parts[1].isdigit():
        imap_uid_hint = parts[1]

    try:
        mail = imaplib.IMAP4_SSL(acc.imap_host, int(acc.imap_port or 993), timeout=45)
        _imap_login(mail, acc, None)
    except Exception:
        return False

    try:
        folders = _pick_folders(mail, full_import=True)
        # Először UID tipp a mappákban
        if imap_uid_hint:
            for folder in folders:
                if not _select_folder(mail, folder):
                    continue
                typ, body_data = mail.fetch(imap_uid_hint.encode(), "(RFC822)")
                if typ != "OK" or not body_data or not body_data[0]:
                    continue
                raw = body_data[0][1]
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                msg = email.message_from_bytes(raw)
                sender = _extract_addr(_decode_header_value(msg.get("From")))
                if sender.lower() != src.email.lower():
                    continue
                body_text, body_html = _parts_from_message(msg)
                if body_html and len(body_html) > 180 and not _is_stub_message(
                    body_text, body_html
                ):
                    return update_message_body(
                        account_id=full.account_id or acc.id,
                        gmail_uid=full.gmail_uid,
                        body_text=body_text,
                        body_html=body_html,
                    )

        # SUBJECT + FROM keresés
        subj = _imap_quote((full.subject or "")[:80])
        from_q = _imap_quote(src.email)
        for folder in folders:
            if not _select_folder(mail, folder):
                continue
            criteria = f'(FROM "{from_q}" SUBJECT "{subj}")'
            typ, data = mail.search(None, criteria)
            if typ != "OK" or not data or not data[0]:
                continue
            for raw_uid in reversed(data[0].split()[-15:]):
                typ, body_data = mail.fetch(raw_uid, "(RFC822)")
                if typ != "OK" or not body_data or not body_data[0]:
                    continue
                raw = body_data[0][1]
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                msg = email.message_from_bytes(raw)
                body_text, body_html = _parts_from_message(msg)
                if body_html and len(body_html) > 180 and not _is_stub_message(
                    body_text, body_html
                ):
                    return update_message_body(
                        account_id=full.account_id or acc.id,
                        gmail_uid=full.gmail_uid,
                        body_text=body_text,
                        body_html=body_html,
                    )
        return False
    finally:
        try:
            mail.logout()
        except Exception:
            pass
