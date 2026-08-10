from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Iterator, Optional

from app.defaults import DEFAULT_SOURCES
from app.paths import CONFIG_EXAMPLE, CONFIG_PATH, DB_PATH, ensure_data_dir


def normalize_subject(subject: str) -> str:
    """Tárgy a DB-be: trim, szóközök, első betű nagy (mondatkezdet)."""
    text = re.sub(r"\s+", " ", (subject or "").strip())
    if not text:
        return "(nincs tárgy)"
    chars = list(text)
    for i, ch in enumerate(chars):
        if ch.isalpha():
            chars[i] = ch.upper()
            break
    return "".join(chars)


def _filename_part(text: str, *, max_len: int) -> str:
    """Fájlnév-darab: emoji/tiltott jelek nélkül."""
    t = (text or "").strip()
    t = re.sub(
        r"[\U0001F000-\U0010FFFF]|[\u2600-\u27BF]|[\uFE0E\uFE0F\u200D\u20E3]",
        "",
        t,
    )
    t = re.sub(r'[\\/:*?"<>|]+', " ", t)
    t = re.sub(r"[^\w\s.\-()áéíóöőúüűÁÉÍÓÖŐÚÜŰ]+", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip(" .-_")
    if not t:
        t = "level"
    if len(t) > max_len:
        t = t[:max_len].rstrip(" .-_")
    return t


def export_filename_stem(
    source_name: str,
    subject: str,
    *,
    when: str = "",
    max_len: int = 100,
) -> str:
    """forrás - Cím - ÉÉÉÉ-HH-NN"""
    src = _filename_part(source_name or "hirlevel", max_len=36)
    title = _filename_part(normalize_subject(subject), max_len=52)
    date = datetime.now().strftime("%Y-%m-%d")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", (when or "").replace("T", " "))
    if m:
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    stem = f"{src} - {title} - {date}"
    if len(stem) > max_len:
        # vágás: forrás + dátum megmarad, cím rövidül
        budget = max_len - len(src) - len(date) - 6  # " - " x2
        title = _filename_part(normalize_subject(subject), max_len=max(12, budget))
        stem = f"{src} - {title} - {date}"
    return stem


@dataclass
class Account:
    id: str
    label: str
    email: str
    app_password: str
    provider: str = "gmail"
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993


@dataclass
class Source:
    id: int
    name: str
    email: str
    account_id: Optional[str]
    active: int
    created_at: str = ""
    tag: str = ""


@dataclass
class Message:
    id: int
    source_id: int
    account_id: str
    gmail_uid: str
    subject: str
    body_text: str
    received_at: str
    created_at: str
    body_html: str = ""
    is_read: int = 1
    is_starred: int = 0


def _source_from_row(row: sqlite3.Row | dict[str, Any]) -> Source:
    data = dict(row)
    data.setdefault("tag", "")
    data.setdefault("created_at", "")
    data["tag"] = str(data.get("tag") or "").strip()
    data["active"] = int(data.get("active") or 0)
    names = {f.name for f in fields(Source)}
    return Source(**{k: data[k] for k in names if k in data})


def _message_from_row(row: sqlite3.Row | dict[str, Any]) -> Message:
    data = dict(row)
    data.setdefault("body_html", "")
    data.setdefault("is_read", 1)
    data.setdefault("is_starred", 0)
    data["is_read"] = int(data.get("is_read") or 0)
    data["is_starred"] = int(data.get("is_starred") or 0)
    names = {f.name for f in fields(Message)}
    return Message(**{k: data[k] for k in names if k in data})


def load_config() -> dict[str, Any]:
    ensure_data_dir()
    if not CONFIG_PATH.exists():
        if CONFIG_EXAMPLE.exists():
            CONFIG_PATH.write_text(CONFIG_EXAMPLE.read_text(encoding="utf-8-sig"), encoding="utf-8")
        else:
            CONFIG_PATH.write_text(
                json.dumps(
                    {
                        "check_interval_minutes": 15,
                        "start_minimized_to_tray": True,
                        "accounts": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
    # utf-8-sig: PowerShell/Notepad BOM-os mentés is működik
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_accounts(cfg: Optional[dict[str, Any]] = None) -> list[Account]:
    from app.imap_providers import resolve_imap

    cfg = cfg or load_config()
    out: list[Account] = []
    for raw in cfg.get("accounts") or []:
        email = (raw.get("email") or "").strip()
        pwd = (raw.get("app_password") or "").strip().replace(" ", "")
        if not email or not pwd or "SAJAT@" in email or pwd.startswith("xxxx"):
            continue
        provider = str(raw.get("provider") or "gmail").strip().lower() or "gmail"
        host, port = resolve_imap(
            provider,
            imap_host=str(raw.get("imap_host") or ""),
            imap_port=raw.get("imap_port"),
        )
        out.append(
            Account(
                id=str(raw.get("id") or email),
                label=str(raw.get("label") or email),
                email=email,
                app_password=pwd,
                provider=provider,
                imap_host=host,
                imap_port=port,
            )
        )
    return out


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                account_id TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                account_id TEXT NOT NULL,
                gmail_uid TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_text TEXT NOT NULL,
                received_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(account_id, gmail_uid),
                FOREIGN KEY(source_id) REFERENCES sources(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_source_received
                ON messages(source_id, received_at DESC);

            CREATE INDEX IF NOT EXISTS idx_messages_fts_ready
                ON messages(subject, received_at);
            """
        )
        _migrate_messages(conn)
        _migrate_sources(conn)
        _migrate_normalize_subjects(conn)
        _seed_sources(conn)


def _migrate_sources(conn: sqlite3.Connection) -> None:
    cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(sources)").fetchall()}
    if "tag" not in cols:
        conn.execute("ALTER TABLE sources ADD COLUMN tag TEXT NOT NULL DEFAULT ''")


def _migrate_messages(conn: sqlite3.Connection) -> None:
    cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(messages)").fetchall()}
    if "body_html" not in cols:
        conn.execute(
            "ALTER TABLE messages ADD COLUMN body_html TEXT NOT NULL DEFAULT ''"
        )
    # Meglévő levelek: olvasottnak számítanak; új import → is_read=0
    if "is_read" not in cols:
        conn.execute(
            "ALTER TABLE messages ADD COLUMN is_read INTEGER NOT NULL DEFAULT 1"
        )
    if "is_starred" not in cols:
        conn.execute(
            "ALTER TABLE messages ADD COLUMN is_starred INTEGER NOT NULL DEFAULT 0"
        )


def _migrate_normalize_subjects(conn: sqlite3.Connection) -> None:
    """Egyszer: meglévő tárgyak mondatkezdet + szóköz tisztítás."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    done = conn.execute(
        "SELECT value FROM app_meta WHERE key = ?",
        ("subjects_normalized_v1",),
    ).fetchone()
    if done:
        return
    rows = conn.execute("SELECT id, subject FROM messages").fetchall()
    for row in rows:
        old = str(row["subject"] or "")
        new = normalize_subject(old)
        if new != old:
            conn.execute(
                "UPDATE messages SET subject = ? WHERE id = ?",
                (new, int(row["id"])),
            )
    conn.execute(
        "INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)",
        ("subjects_normalized_v1", "1"),
    )


def _seed_sources(conn: sqlite3.Connection) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    for item in DEFAULT_SOURCES:
        conn.execute(
            """
            INSERT OR IGNORE INTO sources (name, email, account_id, active, created_at)
            VALUES (?, ?, NULL, 1, ?)
            """,
            (item["name"], item["email"].lower(), now),
        )


def list_sources(active_only: bool = True) -> list[Source]:
    with connect() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT * FROM sources WHERE active = 1 "
                "ORDER BY IFNULL(tag,'') COLLATE NOCASE, name COLLATE NOCASE"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sources "
                "ORDER BY active DESC, IFNULL(tag,'') COLLATE NOCASE, name COLLATE NOCASE"
            ).fetchall()
    return [_source_from_row(r) for r in rows]


def get_source(source_id: int) -> Optional[Source]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    return _source_from_row(row) if row else None


def find_source_by_email(email: str) -> Optional[Source]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM sources WHERE email = ? COLLATE NOCASE",
            (email.lower(),),
        ).fetchone()
    return _source_from_row(row) if row else None


def add_source(name: str, email: str, account_id: Optional[str] = None) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO sources (name, email, account_id, active, created_at)
            VALUES (?, ?, ?, 1, ?)
            """,
            (name.strip(), email.strip().lower(), account_id, now),
        )
        return int(cur.lastrowid)


def rename_source(source_id: int, new_name: str) -> bool:
    name = (new_name or "").strip()
    if not name:
        return False
    with connect() as conn:
        cur = conn.execute(
            "UPDATE sources SET name = ? WHERE id = ?",
            (name, source_id),
        )
        return cur.rowcount > 0


def set_source_active(source_id: int, active: bool) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE sources SET active = ? WHERE id = ?",
            (1 if active else 0, source_id),
        )
        return cur.rowcount > 0


def set_source_tag(source_id: int, tag: str) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE sources SET tag = ? WHERE id = ?",
            ((tag or "").strip(), source_id),
        )
        return cur.rowcount > 0


def insert_message(
    *,
    source_id: int,
    account_id: str,
    gmail_uid: str,
    subject: str,
    body_text: str,
    received_at: datetime,
    body_html: str = "",
) -> bool:
    """True, ha új sor került be."""
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO messages
                (source_id, account_id, gmail_uid, subject, body_text, body_html,
                 received_at, created_at, is_read, is_starred)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
            """,
            (
                source_id,
                account_id,
                gmail_uid,
                normalize_subject(subject),
                body_text or "",
                body_html or "",
                received_at.isoformat(timespec="seconds"),
                now,
            ),
        )
        return cur.rowcount > 0


def get_message(message_id: int) -> Optional[Message]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    if not row:
        return None
    return _message_from_row(row)


def set_message_read(message_id: int, is_read: bool = True) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE messages SET is_read = ? WHERE id = ?",
            (1 if is_read else 0, message_id),
        )


def mark_source_messages_read(source_id: int) -> int:
    """A forrás összes olvasatlan levele → olvasott. Vissza: érintett sorok."""
    with connect() as conn:
        cur = conn.execute(
            "UPDATE messages SET is_read = 1 "
            "WHERE source_id = ? AND IFNULL(is_read, 1) = 0",
            (source_id,),
        )
        return int(cur.rowcount or 0)


def mark_all_messages_read() -> int:
    """Minden olvasatlan levél → olvasott. Vissza: érintett sorok."""
    with connect() as conn:
        cur = conn.execute(
            "UPDATE messages SET is_read = 1 WHERE IFNULL(is_read, 1) = 0"
        )
        return int(cur.rowcount or 0)


def set_message_starred(message_id: int, is_starred: bool) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE messages SET is_starred = ? WHERE id = ?",
            (1 if is_starred else 0, message_id),
        )


def toggle_message_starred(message_id: int) -> bool:
    """Visszaadja az új is_starred állapotot."""
    with connect() as conn:
        row = conn.execute(
            "SELECT is_starred FROM messages WHERE id = ?", (message_id,)
        ).fetchone()
        if not row:
            return False
        new_val = 0 if int(row["is_starred"] or 0) else 1
        conn.execute(
            "UPDATE messages SET is_starred = ? WHERE id = ?",
            (new_val, message_id),
        )
        return bool(new_val)


def list_messages(
    source_id: Optional[int] = None,
    query: str = "",
    limit: int = 500,
    *,
    with_html: bool = False,
    unread_only: bool = False,
    starred_only: bool = False,
    since_date: str = "",
) -> list[Message]:
    q = (query or "").strip()
    params: list[Any] = []
    # Lista nézetben a nagy HTML ne jöjjön át mind
    if with_html:
        sql = "SELECT * FROM messages WHERE 1=1"
    else:
        sql = (
            "SELECT id, source_id, account_id, gmail_uid, subject, body_text, "
            "'' AS body_html, received_at, created_at, "
            "IFNULL(is_read, 1) AS is_read, IFNULL(is_starred, 0) AS is_starred "
            "FROM messages WHERE 1=1"
        )
    if source_id is not None:
        sql += " AND source_id = ?"
        params.append(source_id)
    if unread_only:
        sql += " AND IFNULL(is_read, 1) = 0"
    if starred_only:
        sql += " AND IFNULL(is_starred, 0) = 1"
    since = (since_date or "").strip()
    if since:
        # ÉÉÉÉ-HH-NN vagy ÉÉÉÉ-HH-NNTHH:MM:SS
        sql += " AND received_at >= ?"
        params.append(since if "T" in since else f"{since}T00:00:00")
    if q:
        if with_html:
            sql += " AND (subject LIKE ? OR body_text LIKE ? OR IFNULL(body_html,'') LIKE ?)"
            like = f"%{q}%"
            params.extend([like, like, like])
        else:
            sql += " AND (subject LIKE ? OR body_text LIKE ?)"
            like = f"%{q}%"
            params.extend([like, like])
    sql += " ORDER BY received_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_message_from_row(r) for r in rows]


def count_messages(source_id: Optional[int] = None) -> int:
    with connect() as conn:
        if source_id is None:
            row = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM messages WHERE source_id = ?",
                (source_id,),
            ).fetchone()
    return int(row["c"])


def count_messages_by_source() -> dict[int, int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT source_id, COUNT(*) AS c FROM messages GROUP BY source_id"
        ).fetchall()
    return {int(r["source_id"]): int(r["c"]) for r in rows}


def count_unread_by_source() -> dict[int, int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT source_id, COUNT(*) AS c FROM messages "
            "WHERE IFNULL(is_read, 1) = 0 GROUP BY source_id"
        ).fetchall()
    return {int(r["source_id"]): int(r["c"]) for r in rows}


def known_gmail_uids(account_id: str) -> set[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT gmail_uid FROM messages WHERE account_id = ?",
            (account_id,),
        ).fetchall()
    return {str(r["gmail_uid"]) for r in rows}


def list_message_bodies(account_id: str) -> list[tuple[str, str, str]]:
    """(gmail_uid, body_text, body_html) — stub/HTML frissítéshez."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT gmail_uid, body_text, IFNULL(body_html, '') AS body_html
            FROM messages WHERE account_id = ?
            """,
            (account_id,),
        ).fetchall()
    return [(str(r["gmail_uid"]), str(r["body_text"] or ""), str(r["body_html"] or "")) for r in rows]


def update_message_body(
    *,
    account_id: str,
    gmail_uid: str,
    body_text: str,
    body_html: str,
) -> bool:
    """True, ha frissült egy meglévő sor (HTML / szöveg javítás)."""
    with connect() as conn:
        cur = conn.execute(
            """
            UPDATE messages
            SET body_text = ?, body_html = ?
            WHERE account_id = ? AND gmail_uid = ?
            """,
            (body_text or "", body_html or "", account_id, gmail_uid),
        )
        return cur.rowcount > 0


def insert_messages_bulk(
    rows: list[tuple[int, str, str, str, str, str, datetime]],
) -> int:
    """rows: (source_id, account_id, gmail_uid, subject, body_text, body_html, received_at)."""
    if not rows:
        return 0
    now = datetime.now().isoformat(timespec="seconds")
    payload = [
        (
            source_id,
            account_id,
            gmail_uid,
            normalize_subject(subject),
            body_text or "",
            body_html or "",
            received_at.isoformat(timespec="seconds"),
            now,
        )
        for source_id, account_id, gmail_uid, subject, body_text, body_html, received_at in rows
    ]
    with connect() as conn:
        before = conn.total_changes
        conn.executemany(
            """
            INSERT OR IGNORE INTO messages
                (source_id, account_id, gmail_uid, subject, body_text, body_html,
                 received_at, created_at, is_read, is_starred)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
            """,
            payload,
        )
        return max(0, conn.total_changes - before)
