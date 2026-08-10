from __future__ import annotations

import html as html_lib
import re
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from app.backup import (
    backup_due,
    create_backup_zip,
    default_backup_filename,
    normalize_backup_interval,
    restore_backup_zip,
    run_scheduled_backup,
)
from app.ctk_menu import CTkMenuBar
from app.db import (
    Message,
    Source,
    add_source,
    count_messages_by_source,
    count_unread_by_source,
    export_filename_stem,
    find_source_by_email,
    get_message,
    get_source,
    init_db,
    list_messages,
    list_sources,
    load_config,
    rename_source,
    save_config,
    set_message_read,
    set_source_active,
    set_source_tag,
    mark_source_messages_read,
    mark_all_messages_read,
    toggle_message_starred,
)
from app.export_docx import export_messages_to_docx
from app.export_rich import export_message_to_docx, export_message_to_pdf
from app.gmail_fetch import fetch_all_accounts, refresh_one_message_html, _is_stub_message
from app.paths import CONFIG_PATH
from app.startup import disable_autostart, enable_autostart, is_autostart_enabled

# Középső lista: egyszerre max ennyi buborék, utána „Több betöltése”
PAGE_SIZE = 20
PREVIEW_LINES = 6
PREVIEW_CHARS = 320
PREVIEW_LINE_MAX = 88
LIST_FETCH_LIMIT = 200
URL_RE = re.compile(
    r"(https?://[^\s<>\"'\]\)]+)|(www\.[^\s<>\"'\]\)]+)",
    re.IGNORECASE,
)


class App(ctk.CTk):
    def __init__(self, start_in_tray: bool = False) -> None:
        super().__init__()
        init_db()

        self.title("Hírlevél követő")
        self.geometry("1280x760")
        self.minsize(1040, 620)
        # CTk címsáv-szín beállítás után is maximálva maradjon
        self.after(80, self._maximize)

        self._selected: Optional[Source] = None
        self._syncing = False
        self._tray_icon = None
        self._poll_job: Optional[str] = None
        self._render_token = 0
        self._messages_cache: list[Message] = []
        self._shown_count = 0
        self._last_day: Optional[str] = None
        self._day_index = -1
        self._smear_job: Optional[str] = None
        self._status_ts = 0.0
        self._wrap = 720
        self._source_names: dict[int, str] = {}
        self._global_results = False
        self._selected_msg_id: Optional[int] = None
        self._html_view = None
        self._reader_fallback: Optional[ctk.CTkTextbox] = None
        self._reader_job: Optional[str] = None
        self._reader_token = 0
        self._last_reader_html = ""
        self._placeholder_shown = False
        self._find_query = ""
        self._find_hits: list[dict] = []
        self._find_index = -1
        self._suppress_auto_open = False
        self._filter_mode = "all"  # all | unread | starred
        self._source_buttons: dict[int, ctk.CTkFrame] = {}
        self._source_stat_labels: dict[int, ctk.CTkLabel] = {}
        self._source_name_labels: dict[int, ctk.CTkLabel] = {}
        self._source_badge_job: Optional[str] = None

        cfg0 = load_config()
        appearance = str(cfg0.get("appearance_mode") or "Dark")
        if appearance not in ("Light", "Dark"):
            appearance = "Dark"
        ctk.set_appearance_mode(appearance)
        ctk.set_default_color_theme("blue")
        self._appearance_var = tk.StringVar(value=appearance)
        self._backup_auto_var = tk.BooleanVar(value=bool(cfg0.get("backup_auto")))
        self._backup_freq_var = tk.StringVar(
            value=normalize_backup_interval(cfg0.get("backup_interval"))
        )
        target0 = str(cfg0.get("backup_target") or "local").strip().lower()
        if target0 not in ("local", "gdrive"):
            target0 = "local"
        self._backup_target_var = tk.StringVar(value=target0)
        self._backup_job: Optional[str] = None
        self._backup_running = False

        self._build()
        self._reload_sources()
        self._schedule_poll()
        self._schedule_backup_check()
        self.bind("<Configure>", self._on_root_configure)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # CTk címsáv után is maradjon a tálcára zárás
        self.after(400, lambda: self.protocol("WM_DELETE_WINDOW", self._on_close))
        # Tray ikon előre, hogy az X azonnal működjön
        self.after(600, self._ensure_tray)

        if start_in_tray:
            self.after(200, self._hide_to_tray)
        else:
            # Indításkor csak könnyű inkrementális szinkron (nem full import)
            self.after(1500, self._sync_async)

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(2, weight=1)

        cfg = load_config()
        interval = int(cfg.get("check_interval_minutes") or 15)
        if interval not in (5, 10, 15, 30):
            interval = 15
        self._interval_var = tk.IntVar(value=interval)
        self._autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        self._last_reader_html = ""
        self._compact = False
        self._reader_focus = False
        self._layout_w = 0

        self._build_menubar()

        # Keresősáv — teljes szélesség
        top_bar = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray18"))
        top_bar.grid(row=1, column=0, columnspan=3, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top_bar,
            text="Keresés",
            font=ctk.CTkFont(family="Candara", size=14, weight="bold"),
        ).grid(row=0, column=0, padx=(16, 8), pady=12)

        self.search = ctk.CTkEntry(
            top_bar,
            placeholder_text="Keresés a hírlevelekben — tárgy és szöveg…",
            height=34,
        )
        self.search.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=12)
        self.search.bind("<Return>", lambda _e: self._run_search())

        ctk.CTkButton(top_bar, text="Keres", width=90, command=self._run_search).grid(
            row=0, column=2, padx=(0, 8), pady=12
        )
        ctk.CTkButton(top_bar, text="Törlés", width=70, command=self._clear_search).grid(
            row=0, column=3, padx=(0, 8), pady=12
        )

        find_nav = ctk.CTkFrame(top_bar, fg_color="transparent")
        find_nav.grid(row=0, column=4, padx=(0, 8), pady=12)
        self.find_prev_btn = ctk.CTkButton(
            find_nav, text="◀", width=34, height=32, command=self._find_prev, state="disabled"
        )
        self.find_prev_btn.pack(side="left", padx=(0, 4))
        self.find_label = ctk.CTkLabel(
            find_nav, text="", width=90, anchor="center", text_color=("gray30", "gray70")
        )
        self.find_label.pack(side="left", padx=2)
        self.find_next_btn = ctk.CTkButton(
            find_nav, text="▶", width=34, height=32, command=self._find_next, state="disabled"
        )
        self.find_next_btn.pack(side="left", padx=(4, 0))

        ctk.CTkButton(top_bar, text="Most ellenőriz", width=120, command=self._sync_async).grid(
            row=0, column=5, padx=(0, 8), pady=12
        )

        self.search_only_selected_var = tk.BooleanVar(value=False)
        self.search_scope_cb = ctk.CTkCheckBox(
            top_bar,
            text="Csak a kiválasztottban",
            variable=self.search_only_selected_var,
        )
        self.search_scope_cb.grid(row=0, column=6, padx=(0, 16), pady=12)

        # --- Bal: hírlevelek ---
        left = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=("gray88", "gray16"))
        left.grid(row=2, column=0, sticky="nsw")
        left.grid_propagate(False)
        self._left_pane = left

        ctk.CTkLabel(
            left,
            text="Hírlevelek",
            font=self._title_font(18),
        ).pack(anchor="w", padx=16, pady=(18, 6))
        ctk.CTkLabel(
            left,
            text="Válassz egy küldőt",
            font=self._body_font(12),
            text_color=("gray45", "gray65"),
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self.source_list = ctk.CTkScrollableFrame(
            left, width=230, fg_color=("gray88", "gray16")
        )
        self.source_list.pack(fill="both", expand=True, padx=8, pady=4)
        self._configure_fast_scroll(self.source_list, step=48)

        ctk.CTkButton(
            left, text="+ Új hírlevél", height=36, command=self._add_newsletter
        ).pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkButton(
            left,
            text="Elrejtettek…",
            height=30,
            fg_color=("gray80", "gray28"),
            command=self._manage_hidden_sources,
        ).pack(fill="x", padx=12, pady=(0, 12))

        # --- Közép: levélbuborékok ---
        mid = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        mid.grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=10)
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_rowconfigure(2, weight=1)
        self._mid_pane = mid

        header_row = ctk.CTkFrame(mid, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", pady=(2, 4))
        header_row.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkLabel(
            header_row,
            text="Hírlevél követő",
            font=self._title_font(22),
            anchor="w",
        )
        self.header.grid(row=0, column=0, sticky="w")

        header_actions = ctk.CTkFrame(header_row, fg_color="transparent")
        header_actions.grid(row=0, column=1, sticky="e")
        self.rename_btn = ctk.CTkButton(
            header_actions, text="Átnevezés", width=90, command=self._rename_selected
        )
        self.rename_btn.pack(side="left", padx=(6, 0))
        self.tag_btn = ctk.CTkButton(
            header_actions, text="Címke", width=70, command=self._tag_selected
        )
        self.tag_btn.pack(side="left", padx=(6, 0))
        self.hide_btn = ctk.CTkButton(
            header_actions, text="Elrejtés", width=80, command=self._hide_selected
        )
        self.hide_btn.pack(side="left", padx=(6, 0))
        self.mark_read_btn = ctk.CTkButton(
            header_actions,
            text="Olvasottnak jelöl",
            width=130,
            command=self._mark_selected_all_read,
        )
        self.mark_read_btn.pack(side="left", padx=(6, 0))
        self.export_btn = ctk.CTkButton(
            header_actions, text="Word lista", width=100, command=self._export
        )
        self.export_btn.pack(side="left", padx=(6, 0))
        self.export_pdf_btn = ctk.CTkButton(
            header_actions, text="PDF lista", width=90, command=self._export_list_pdf
        )
        self.export_pdf_btn.pack(side="left", padx=(6, 0))

        filter_row = ctk.CTkFrame(mid, fg_color="transparent")
        filter_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self._filter_var = tk.StringVar(value="all")
        for value, label in (
            ("all", "Összes"),
            ("unread", "Olvasatlan"),
            ("starred", "★ Kedvenc"),
        ):
            ctk.CTkRadioButton(
                filter_row,
                text=label,
                variable=self._filter_var,
                value=value,
                command=self._apply_list_filter,
                width=90,
            ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(filter_row, text="Dátumtól:", font=self._body_font(12)).pack(
            side="left", padx=(8, 4)
        )
        self.since_entry = ctk.CTkEntry(
            filter_row, width=110, height=28, placeholder_text="ÉÉÉÉ-HH-NN"
        )
        self.since_entry.pack(side="left", padx=(0, 6))
        self.since_entry.bind("<Return>", lambda _e: self._apply_list_filter())
        ctk.CTkButton(
            filter_row, text="Szűr", width=56, height=28, command=self._apply_list_filter
        ).pack(side="left")

        # Folyamatos görgetés a betöltött buborékokon; 20 után „Több betöltése”
        self.msg_frame = ctk.CTkScrollableFrame(
            mid, fg_color=("gray96", "gray14")
        )
        self.msg_frame.grid(row=2, column=0, sticky="nsew")
        self._configure_msg_scroll(self.msg_frame)

        self.status = ctk.CTkLabel(mid, text="", anchor="w", text_color=("gray40", "gray70"))
        self.status.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        # --- Jobb: HTML olvasó ---
        reader_wrap = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray92", "gray14"))
        reader_wrap.grid(row=2, column=2, sticky="nsew", padx=(4, 10), pady=10)
        reader_wrap.grid_columnconfigure(0, weight=1)
        reader_wrap.grid_rowconfigure(1, weight=1)
        self._reader_pane = reader_wrap

        reader_head = ctk.CTkFrame(reader_wrap, fg_color="transparent")
        reader_head.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        reader_head.grid_columnconfigure(1, weight=1)

        self.back_to_list_btn = ctk.CTkButton(
            reader_head,
            text="← Lista",
            width=80,
            height=28,
            command=self._back_to_list,
        )
        self.back_to_list_btn.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.back_to_list_btn.grid_remove()

        self.reader_title = ctk.CTkLabel(
            reader_head,
            text="Olvasó",
            font=self._title_font(16),
            anchor="w",
        )
        self.reader_title.grid(row=0, column=1, sticky="w")

        self.browser_btn = ctk.CTkButton(
            reader_head,
            text="Böngészőben",
            width=110,
            height=28,
            command=self._open_reader_in_browser,
        )
        self.browser_btn.grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.links_btn = ctk.CTkButton(
            reader_head,
            text="Linkek",
            width=70,
            height=28,
            command=self._show_reader_links,
        )
        self.links_btn.grid(row=0, column=3, sticky="e", padx=(8, 0))
        self.reader_word_btn = ctk.CTkButton(
            reader_head,
            text="Word",
            width=64,
            height=28,
            command=lambda: self._export_current("docx"),
        )
        self.reader_word_btn.grid(row=0, column=4, sticky="e", padx=(8, 0))
        self.reader_pdf_btn = ctk.CTkButton(
            reader_head,
            text="PDF",
            width=56,
            height=28,
            command=lambda: self._export_current("pdf"),
        )
        self.reader_pdf_btn.grid(row=0, column=5, sticky="e", padx=(8, 0))

        self.reader_host = ctk.CTkFrame(
            reader_wrap, fg_color=("gray96", "gray12"), corner_radius=12
        )
        self.reader_host.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.reader_host.grid_columnconfigure(0, weight=1)
        self.reader_host.grid_rowconfigure(0, weight=1)
        self._init_html_reader()
        self._show_reader_placeholder()
        self._show_list_empty_state("welcome")

    def _title_font(self, size: int = 18) -> ctk.CTkFont:
        for family in ("Candara", "Calibri", "Segoe UI Semibold", "Segoe UI"):
            try:
                return ctk.CTkFont(family=family, size=size, weight="bold")
            except Exception:
                continue
        return ctk.CTkFont(size=size, weight="bold")

    def _body_font(self, size: int = 13) -> ctk.CTkFont:
        for family in ("Calibri", "Candara", "Segoe UI"):
            try:
                return ctk.CTkFont(family=family, size=size)
            except Exception:
                continue
        return ctk.CTkFont(size=size)

    def _on_root_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if event.widget is not self:
            return
        w = int(event.width or 0)
        if abs(w - self._layout_w) < 24:
            return
        self._layout_w = w
        compact = w > 0 and w < 1080
        if compact != self._compact:
            self._compact = compact
            if not compact:
                self._reader_focus = False
            self._apply_layout_mode()

    def _apply_layout_mode(self) -> None:
        """Széles: 3 oszlop. Keskeny: lista VAGY olvasó (+ Vissza)."""
        left = self._left_pane
        mid = self._mid_pane
        reader = self._reader_pane
        if not self._compact:
            left.grid(row=2, column=0, sticky="nsw")
            mid.grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=10)
            reader.grid(row=2, column=2, sticky="nsew", padx=(4, 10), pady=10)
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=2)
            self.back_to_list_btn.grid_remove()
            return
        left.grid(row=2, column=0, sticky="nsw")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        if self._reader_focus and self._selected_msg_id is not None:
            mid.grid_remove()
            reader.grid(row=2, column=1, sticky="nsew", padx=(8, 10), pady=10)
            self.back_to_list_btn.grid()
        else:
            reader.grid_remove()
            mid.grid(row=2, column=1, sticky="nsew", padx=(8, 10), pady=10)
            self.back_to_list_btn.grid_remove()

    def _back_to_list(self) -> None:
        self._reader_focus = False
        self._apply_layout_mode()

    def _show_list_empty_state(self, kind: str = "welcome") -> None:
        for w in self.msg_frame.winfo_children():
            w.destroy()
        box = ctk.CTkFrame(self.msg_frame, fg_color=("gray90", "gray20"), corner_radius=16)
        box.pack(fill="x", padx=16, pady=24)
        if kind == "welcome":
            title = "Kezdés három lépésben"
            body = (
                "1. Levelezés → Levelező fiókok… (IMAP)\n"
                "2. Bal oldalon válassz vagy adj hozzá hírlevelet\n"
                "3. A középső listából nyisd meg a levelet az olvasóban"
            )
        elif kind == "no_source":
            title = "Válassz hírlevelet"
            body = "Kattints bal oldalon egy küldőre, vagy keress felül."
        elif kind == "no_mail":
            title = "Nincs megjeleníthető levél"
            body = "Próbáld a „Most ellenőriz” gombot, vagy a teljes előzmény importot."
        else:
            title = "Nincs találat"
            body = "Próbálj másik keresőszót."
        ctk.CTkLabel(
            box, text=title, font=self._title_font(17), anchor="w"
        ).pack(anchor="w", padx=18, pady=(16, 6))
        ctk.CTkLabel(
            box,
            text=body,
            font=self._body_font(13),
            text_color=("gray40", "gray70"),
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(0, 16))

    def _reader_placeholder_html(self) -> str:
        bg, fg = self._reader_theme_colors()
        return (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>body{{background:{bg};color:#888;font-family:Calibri,Candara,Segoe UI,sans-serif;"
            f"padding:28px;line-height:1.5}}</style></head><body>"
            f"<h2 style='color:{fg};font-family:Candara,Calibri,sans-serif;font-weight:600;margin:0 0 8px'>Olvasópanel</h2>"
            f"<p>Itt jelenik meg a hírlevél HTML nézete — mint a levelezőben.</p>"
            f"<p>Válassz egy buborékot a középső listából.</p>"
            f"</body></html>"
        )

    def _show_reader_placeholder(self) -> None:
        self.reader_title.configure(text="Olvasó")
        if self._placeholder_shown and self._selected_msg_id is None:
            return
        html = self._reader_placeholder_html()
        self._last_reader_html = html
        self._placeholder_shown = True
        if self._html_view is not None:
            try:
                self._html_view.load_html(html)
            except Exception:
                pass
        elif self._reader_fallback is not None:
            self._reader_fallback.configure(state="normal")
            self._reader_fallback.delete("1.0", "end")
            self._reader_fallback.insert("1.0", "Válassz egy levelet a listából.")
            self._reader_fallback.configure(state="disabled")

    def _reader_loading_html(self) -> str:
        bg, fg = self._reader_theme_colors()
        return (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>body{{background:{bg};color:#888;font-family:'Segoe UI',sans-serif;"
            f"padding:28px}}</style></head><body>"
            f"<p style='color:{fg}'>Betöltés…</p></body></html>"
        )

    def _open_reader_in_browser(self) -> None:
        html = (self._last_reader_html or "").strip()
        if not html:
            self._set_status("Nincs megnyitható levél az olvasóban.", force=True)
            return
        import tempfile
        from pathlib import Path

        path = Path(tempfile.gettempdir()) / "hirlevel_olvaso.html"
        path.write_text(html, encoding="utf-8")
        webbrowser.open(path.as_uri())

    def _init_html_reader(self) -> None:
        try:
            from tkinterweb import HtmlFrame

            def _on_link(url: str) -> None:
                if not url:
                    return
                u = url.strip()
                if u.lower().startswith("www."):
                    u = "https://" + u
                if u.startswith("http://") or u.startswith("https://") or u.startswith("mailto:"):
                    webbrowser.open(u)

            self._html_view = HtmlFrame(
                self.reader_host,
                messages_enabled=False,
                vertical_scrollbar=True,
                horizontal_scrollbar=False,
                on_link_click=_on_link,
            )
            self._html_view.grid(row=0, column=0, sticky="nsew")
        except Exception:
            self._html_view = None
            self._reader_fallback = ctk.CTkTextbox(self.reader_host, wrap="word")
            self._reader_fallback.grid(row=0, column=0, sticky="nsew")
            self._reader_fallback.insert(
                "1.0",
                "HTML olvasó nem elérhető (tkinterweb). Szöveges mód aktív.",
            )
            self._reader_fallback.configure(state="disabled")

    @staticmethod
    def _plain_text_to_linked_html(text: str) -> str:
        """Sima szöveg → HTML, http(s)/www URL-ek kattintható <a> linkkel."""
        raw = text or ""
        parts: list[str] = []
        pos = 0
        for match in URL_RE.finditer(raw):
            start, end = match.span()
            if start > pos:
                parts.append(html_lib.escape(raw[pos:start]))
            url_raw = match.group(0)
            # záró írásjelek levágása a linkből
            trail = ""
            clean = url_raw
            while clean and clean[-1] in ".,;:!?)]}>\"'":
                trail = clean[-1] + trail
                clean = clean[:-1]
            href = clean
            if href.lower().startswith("www."):
                href = "https://" + href
            parts.append(
                f'<a href="{html_lib.escape(href, quote=True)}">'
                f"{html_lib.escape(clean)}</a>{html_lib.escape(trail)}"
            )
            pos = end
        if pos < len(raw):
            parts.append(html_lib.escape(raw[pos:]))
        body = "".join(parts).replace("\n", "<br>\n")
        return f'<div style="white-space:normal;word-break:break-word">{body}</div>'

    def _reader_theme_colors(self) -> tuple[str, str]:
        """Üres/betöltő nézet — követi az app témát."""
        if ctk.get_appearance_mode() == "Dark":
            return "#1a1d23", "#e8eaed"
        return "#f4f6f8", "#1a1a1a"

    def _reader_letter_colors(self) -> tuple[str, str]:
        """Hírlevél HTML: mindig világos „papír”, mert a levelek sötét szövegre készültek."""
        return "#F3F1EC", "#1a1a1a"

    def _wrap_reader_html(self, html: str) -> str:
        bg, fg = self._reader_letter_colors()
        raw = (html or "").strip()
        style = (
            f"<style>html,body{{background:{bg} !important;color:{fg} !important;"
            f"font-family:Calibri,Candara,Segoe UI,sans-serif;margin:0;padding:16px;line-height:1.5}}"
            f"h1,h2,h3,p,li,td,th,div,span{{color:inherit}}"
            f"h1,h2,h3{{font-family:Candara,Calibri,sans-serif}}"
            f"a{{color:#0B57D0 !important;text-decoration:underline}}"
            f"img{{max-width:100%;height:auto}}"
            f"mark.find-hit{{background:#F5D76E;color:#111;padding:0 2px;border-radius:2px}}"
            f"mark.find-current{{background:#FF9800;color:#111;padding:0 2px;border-radius:2px;"
            f"outline:2px solid #E65100}}</style>"
        )
        if not raw:
            return (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>{style}</head>"
                f"<body style='color:#666'>Nincs megjeleníthető tartalom.</body></html>"
            )
        lower = raw.lower()
        if "<html" in lower:
            if "<head" in lower:
                return raw.replace("<head>", f"<head>{style}", 1)
            return raw.replace("<html>", f"<html><head><meta charset='utf-8'>{style}</head>", 1)
        return (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>{style}</head>"
            f"<body>{raw}</body></html>"
        )

    @staticmethod
    def _collect_find_hits(messages: list[Message], query: str) -> list[dict]:
        """Találatok: minden előfordulás (tárgy + szöveg), sorrendben."""
        q = (query or "").strip()
        if not q:
            return []
        q_lower = q.lower()
        hits: list[dict] = []
        for msg in messages:
            for where, text in (("subject", msg.subject or ""), ("body", msg.body_text or "")):
                lower = text.lower()
                start = 0
                while True:
                    i = lower.find(q_lower, start)
                    if i < 0:
                        break
                    hits.append(
                        {
                            "msg_id": msg.id,
                            "where": where,
                            "start": i,
                            "end": i + len(q),
                        }
                    )
                    start = i + max(1, len(q_lower))
        return hits

    @staticmethod
    def _highlight_plain_html(
        text: str,
        query: str,
        *,
        current_start: Optional[int] = None,
        current_where: str = "body",
        where: str = "body",
    ) -> str:
        """Sima szöveg → HTML, keresőszó kiemeléssel."""
        raw = text or ""
        q = (query or "").strip()
        if not q:
            return App._plain_text_to_linked_html(raw)

        pattern = re.compile(re.escape(q), re.IGNORECASE)
        parts: list[str] = []
        pos = 0
        for match in pattern.finditer(raw):
            if match.start() > pos:
                parts.append(html_lib.escape(raw[pos : match.start()]).replace("\n", "<br>\n"))
            is_current = (
                where == current_where
                and current_start is not None
                and match.start() == current_start
            )
            cls = "find-current" if is_current else "find-hit"
            aid = ' id="find-current"' if is_current else ""
            parts.append(
                f'<mark class="{cls}"{aid}>{html_lib.escape(match.group(0))}</mark>'
            )
            pos = match.end()
        if pos < len(raw):
            parts.append(html_lib.escape(raw[pos:]).replace("\n", "<br>\n"))
        body = "".join(parts)
        return f'<div style="white-space:normal;word-break:break-word">{body}</div>'

    def _clear_find(self) -> None:
        self._find_query = ""
        self._find_hits = []
        self._find_index = -1
        self._update_find_nav()

    def _update_find_nav(self) -> None:
        n = len(self._find_hits)
        if n <= 0 or self._find_index < 0:
            self.find_label.configure(text="")
            self.find_prev_btn.configure(state="disabled")
            self.find_next_btn.configure(state="disabled")
            return
        self.find_label.configure(text=f"{self._find_index + 1} / {n}")
        self.find_prev_btn.configure(state="normal")
        self.find_next_btn.configure(state="normal")

    def _find_prev(self) -> None:
        if not self._find_hits:
            return
        self._find_index = (self._find_index - 1) % len(self._find_hits)
        self._goto_find_hit()

    def _find_next(self) -> None:
        if not self._find_hits:
            return
        self._find_index = (self._find_index + 1) % len(self._find_hits)
        self._goto_find_hit()

    def _goto_find_hit(self) -> None:
        if not self._find_hits or self._find_index < 0:
            return
        hit = self._find_hits[self._find_index]
        self._update_find_nav()
        letters = len(self._find_hits)
        self._set_status(
            f"Találat {self._find_index + 1}/{letters} — „{self._find_query}”",
            force=True,
        )
        msg_id = int(hit["msg_id"])
        select_idx = self._find_select_index(hit)
        # Ugyanaz a levél: ne töltsük újra, csak ugorjunk a következő szóra
        if (
            self._selected_msg_id == msg_id
            and self._html_view is not None
            and self._find_query
        ):
            self._scroll_to_find(
                self._find_query,
                select_idx,
                self._reader_token,
                use_anchor=False,
            )
            return
        self._show_message_in_reader(msg_id, find_hit=hit)

    def _find_select_index(self, hit: dict) -> int:
        """Hányadik előfordulás ez a leveleken belül (1-alapú, find_text-hez)."""
        msg_id = int(hit["msg_id"])
        same = [h for h in self._find_hits if int(h["msg_id"]) == msg_id]
        for i, h in enumerate(same):
            if h.get("where") == hit.get("where") and int(h.get("start", -1)) == int(
                hit.get("start", -2)
            ):
                return i + 1
        return 1

    def _scroll_to_find(
        self,
        query: str,
        select: int,
        token: int,
        *,
        use_anchor: bool = True,
        attempt: int = 0,
    ) -> None:
        """Rágörget a találatra: #find-current és/vagy tkinterweb find_text."""
        if token != self._reader_token or self._html_view is None:
            return
        ok = False
        if use_anchor:
            try:
                el = self._html_view.document.getElementById("find-current")
                if el is not None:
                    el.scrollIntoView()
                    ok = True
            except Exception:
                pass
        q = (query or "").strip()
        if q:
            try:
                pattern = re.escape(q)
                n = int(
                    self._html_view.find_text(
                        pattern,
                        select=1,
                        ignore_case=True,
                        highlight_all=True,
                    )
                    or 0
                )
                if n <= 0:
                    n = int(
                        self._html_view.find_text(
                            q, select=1, ignore_case=True, highlight_all=True
                        )
                        or 0
                    )
                    pattern = q
                if n > 0:
                    sel = min(max(1, int(select)), n)
                    if sel != 1:
                        self._html_view.find_text(
                            pattern,
                            select=sel,
                            ignore_case=True,
                            highlight_all=True,
                        )
                    ok = True
            except Exception:
                pass
        if not ok and attempt < 5:
            self.after(
                160,
                lambda: self._scroll_to_find(
                    query,
                    select,
                    token,
                    use_anchor=use_anchor,
                    attempt=attempt + 1,
                ),
            )

    def _ensure_msg_visible(self, msg_id: int) -> None:
        """Ha a levél még nincs kirajzolva, betölti a következő 20-asokat, amíg eléri."""
        idx = next((i for i, m in enumerate(self._messages_cache) if m.id == msg_id), -1)
        if idx < 0:
            return
        token = self._render_token
        while self._shown_count <= idx and self._shown_count < len(self._messages_cache):
            self._render_next_page(token)
        # Ne ugorjunk a lista tetejére — csak a kártyához görgetünk, ha megvan
        try:
            for w in self.msg_frame.winfo_children():
                if getattr(w, "_msg_id", None) == msg_id:
                    self.msg_frame.update_idletasks()
                    canvas = self.msg_frame._parent_canvas  # noqa: SLF001
                    # kártya a canvasban: ha a látható terület alatt/fölött van, igazítunk
                    y = w.winfo_y()
                    h = max(self.msg_frame.winfo_height(), 1)
                    total = max(canvas.bbox("all")[3] if canvas.bbox("all") else h, 1)
                    if y > h * 0.7 or y < 0:
                        canvas.yview_moveto(max(0.0, min(1.0, (y - 20) / total)))
                    break
        except Exception:
            pass

    def _show_message_in_reader(
        self, msg_id: int, *, find_hit: Optional[dict] = None
    ) -> None:
        """Debounce + DB háttérszál — a HTML parse a UI szálon marad, de nem egymásra."""
        msg_id = int(msg_id)
        self._selected_msg_id = msg_id
        self._placeholder_shown = False
        self._ensure_msg_visible(msg_id)
        self._mark_message_read(msg_id)
        self._apply_bubble_styles()
        if self._compact:
            self._reader_focus = True
            self._apply_layout_mode()
        if self._reader_job is not None:
            try:
                self.after_cancel(self._reader_job)
            except Exception:
                pass
            self._reader_job = None

        self._reader_token += 1
        token = self._reader_token
        query = self._find_query if find_hit else ""
        select_idx = self._find_select_index(find_hit) if find_hit else 1

        def start() -> None:
            if token != self._reader_token:
                return
            self.reader_title.configure(text="Betöltés…")

            def work() -> None:
                try:
                    full = get_message(msg_id)
                except Exception as exc:
                    self.after(
                        0,
                        lambda: self._set_status(f"Olvasó hiba: {exc}", force=True)
                        if token == self._reader_token
                        else None,
                    )
                    return
                if not full:
                    return

                # Stub (can't display HTML) → azonnali IMAP HTML-frissítés
                if _is_stub_message(full.body_text or "", full.body_html or ""):
                    self.after(
                        0,
                        lambda: self._set_status(
                            "HTML hiányzik — letöltés a levelezőből…", force=True
                        )
                        if token == self._reader_token
                        else None,
                    )
                    try:
                        if refresh_one_message_html(msg_id):
                            full = get_message(msg_id) or full
                            self.after(
                                0,
                                lambda: self._set_status("HTML betöltve.", force=True)
                                if token == self._reader_token
                                else None,
                            )
                        else:
                            self.after(
                                0,
                                lambda: self._set_status(
                                    "Nem sikerült a HTML — próbáld: Teljes előzmény import",
                                    force=True,
                                )
                                if token == self._reader_token
                                else None,
                            )
                    except Exception as exc:
                        self.after(
                            0,
                            lambda: self._set_status(f"HTML frissítés hiba: {exc}", force=True)
                            if token == self._reader_token
                            else None,
                        )

                subject = full.subject or "(nincs tárgy)"
                body_text = full.body_text or "(nincs tartalom)"

                if find_hit and query:
                    # Keresés: szöveges nézet (találatszám egyezik) + find_text görgetés
                    cur_start = int(find_hit["start"])
                    cur_where = str(find_hit["where"])
                    subj_html = self._highlight_plain_html(
                        subject,
                        query,
                        current_start=cur_start if cur_where == "subject" else None,
                        current_where=cur_where,
                        where="subject",
                    )
                    body_html_view = self._highlight_plain_html(
                        body_text,
                        query,
                        current_start=cur_start if cur_where == "body" else None,
                        current_where=cur_where,
                        where="body",
                    )
                    html = (
                        f"<h2 style='margin:0 0 12px;font-size:1.15em'>{subj_html}</h2>"
                        f"{body_html_view}"
                    )
                    html = self._wrap_reader_html(html)
                else:
                    html = (full.body_html or "").strip()
                    if not html:
                        html = self._plain_text_to_linked_html(body_text)
                    html = self._wrap_reader_html(html)

                def apply() -> None:
                    if token != self._reader_token:
                        return
                    title = subject
                    if find_hit and query:
                        title = f"🔍 {subject}"
                    self.reader_title.configure(text=title)
                    self._last_reader_html = html
                    if self._html_view is not None:
                        try:
                            # Előző keresőkiemelés törlése
                            try:
                                self._html_view.find_text("")
                            except Exception:
                                pass
                            self._html_view.load_html(html)
                            if find_hit and query:
                                self.after(
                                    280,
                                    lambda: self._scroll_to_find(
                                        query,
                                        select_idx,
                                        token,
                                        use_anchor=True,
                                    ),
                                )
                        except Exception as exc:
                            self._set_status(f"HTML megjelenítés hiba: {exc}", force=True)
                    elif self._reader_fallback is not None:
                        self._reader_fallback.configure(state="normal")
                        self._reader_fallback.delete("1.0", "end")
                        self._reader_fallback.insert("1.0", body_text)
                        self._reader_fallback.configure(state="disabled")

                self.after(0, apply)

            threading.Thread(target=work, daemon=True).start()

        self._reader_job = self.after(80, start)

    def _clear_msg_frame(self) -> None:
        for w in self.msg_frame.winfo_children():
            w.destroy()
        # Ne töltsünk újra placeholder HTML-t minden listaváltáskor (lassú)
        if self._reader_job is not None:
            try:
                self.after_cancel(self._reader_job)
            except Exception:
                pass
            self._reader_job = None
        self._reader_token += 1
        self._selected_msg_id = None

    @staticmethod
    def _bubble_preview(text: str) -> tuple[str, bool]:
        """Rövid előnézet; hosszú URL-sorok levágva (ne fújja szét a listát)."""
        raw = (text or "").strip()
        if not raw:
            return "(nincs előnézet)", False
        lines = raw.splitlines()
        nonempty = [ln for ln in lines if ln.strip()]
        if len(nonempty) <= PREVIEW_LINES and len(raw) <= PREVIEW_CHARS:
            clipped = []
            for ln in lines:
                s = ln.strip()
                if len(s) > PREVIEW_LINE_MAX:
                    s = s[: PREVIEW_LINE_MAX - 1] + "…"
                clipped.append(s if ln.strip() else "")
            return "\n".join(clipped).strip() or "(nincs előnézet)", False
        shown: list[str] = []
        count = 0
        for ln in lines:
            s = ln.rstrip()
            if len(s) > PREVIEW_LINE_MAX:
                s = s[: PREVIEW_LINE_MAX - 1] + "…"
            shown.append(s)
            if ln.strip():
                count += 1
            if count >= PREVIEW_LINES:
                break
        preview = "\n".join(shown).strip()
        if len(preview) > PREVIEW_CHARS:
            preview = preview[: PREVIEW_CHARS - 1].rstrip() + "…"
        elif count >= PREVIEW_LINES or len(nonempty) > PREVIEW_LINES:
            preview = preview.rstrip() + "\n…"
        return preview, True

    def _configure_fast_scroll(
        self, scrollable: ctk.CTkScrollableFrame, *, step: int = 80
    ) -> None:
        """Bal oldali forráslista görgetése."""
        del step
        canvas = scrollable._parent_canvas  # noqa: SLF001
        try:
            canvas.configure(yscrollincrement=2, xscrollincrement=2)
        except Exception:
            pass

    def _configure_msg_scroll(self, scrollable: ctk.CTkScrollableFrame) -> None:
        """CTk alap görgetés — ne hide/show (az villogást okoz)."""
        canvas = scrollable._parent_canvas  # noqa: SLF001
        try:
            canvas.configure(yscrollincrement=2, xscrollincrement=2)
        except Exception:
            pass

    def _scroll_messages(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """Textbox fölött: tovább a lista canvasára."""
        canvas = self.msg_frame._parent_canvas  # noqa: SLF001
        try:
            if sys.platform.startswith("win"):
                amount = -int(event.delta / 6) or (-1 if event.delta > 0 else 1)
                canvas.yview_scroll(amount, "units")
            elif sys.platform == "darwin":
                canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                canvas.yview_scroll(-1 if getattr(event, "num", 0) == 4 else 1, "units")
        except Exception:
            pass
        return "break"

    def _reset_scroll(self, scrollable: ctk.CTkScrollableFrame) -> None:
        canvas = scrollable._parent_canvas  # noqa: SLF001
        try:
            scrollable.update_idletasks()
            bbox = canvas.bbox("all")
            canvas.configure(scrollregion=bbox if bbox else (0, 0, 0, 0))
            canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _build_menubar(self) -> None:
        # Natív Windows menü helyett CTk sáv — követi a Light/Dark témát
        self.configure(menu="")
        menus = [
            (
                "Fájl",
                [
                    {
                        "kind": "command",
                        "label": "Mentés biztonsági másolat…",
                        "command": self._backup_export,
                    },
                    {
                        "kind": "command",
                        "label": "Visszaállítás backupból…",
                        "command": self._backup_restore,
                    },
                    {"kind": "separator"},
                    {
                        "kind": "command",
                        "label": "Tálcára (ablak bezárása)",
                        "command": self._hide_to_tray,
                    },
                    {"kind": "command", "label": "Kilépés", "command": self._quit_app},
                ],
            ),
            (
                "Levelezés",
                [
                    {"kind": "command", "label": "Levelező fiókok…", "command": self._open_accounts},
                    {"kind": "command", "label": "Új hírlevél felvétel", "command": self._add_newsletter},
                    {"kind": "separator"},
                    {"kind": "command", "label": "Most ellenőriz", "command": self._sync_async},
                    {
                        "kind": "command",
                        "label": "Teljes előzmény import",
                        "command": self._full_import_async,
                    },
                    {"kind": "separator"},
                    {
                        "kind": "command",
                        "label": "Aktuális hírlevél olvasottnak",
                        "command": self._mark_selected_all_read,
                    },
                    {
                        "kind": "command",
                        "label": "Minden olvasatlan olvasottnak",
                        "command": self._mark_everything_read,
                    },
                ],
            ),
            (
                "Beállítások",
                [
                    {
                        "kind": "submenu",
                        "label": "Frissítési intervallum",
                        "items": [
                            {
                                "kind": "radio",
                                "label": f"{m} perc",
                                "variable": self._interval_var,
                                "value": m,
                                "command": self._apply_interval,
                            }
                            for m in (5, 10, 15, 30)
                        ],
                    },
                    {
                        "kind": "submenu",
                        "label": "Téma",
                        "items": [
                            {
                                "kind": "radio",
                                "label": "Világos",
                                "variable": self._appearance_var,
                                "value": "Light",
                                "command": self._apply_appearance,
                            },
                            {
                                "kind": "radio",
                                "label": "Sötét",
                                "variable": self._appearance_var,
                                "value": "Dark",
                                "command": self._apply_appearance,
                            },
                        ],
                    },
                    {
                        "kind": "check",
                        "label": "Windows indításkor induljon",
                        "variable": self._autostart_var,
                        "command": self._apply_autostart,
                    },
                    {"kind": "separator"},
                    {
                        "kind": "check",
                        "label": "Automata biztonsági mentés",
                        "variable": self._backup_auto_var,
                        "command": self._apply_backup_auto,
                    },
                    {
                        "kind": "submenu",
                        "label": "Mentés helye",
                        "items": [
                            {
                                "kind": "radio",
                                "label": "Gépre (mappa)",
                                "variable": self._backup_target_var,
                                "value": "local",
                                "command": self._apply_backup_target,
                            },
                            {
                                "kind": "radio",
                                "label": "Google Drive",
                                "variable": self._backup_target_var,
                                "value": "gdrive",
                                "command": self._apply_backup_target,
                            },
                        ],
                    },
                    {
                        "kind": "submenu",
                        "label": "Mentés gyakorisága",
                        "items": [
                            {
                                "kind": "radio",
                                "label": "Napi",
                                "variable": self._backup_freq_var,
                                "value": "daily",
                                "command": self._apply_backup_freq,
                            },
                            {
                                "kind": "radio",
                                "label": "Heti",
                                "variable": self._backup_freq_var,
                                "value": "weekly",
                                "command": self._apply_backup_freq,
                            },
                            {
                                "kind": "radio",
                                "label": "Havi",
                                "variable": self._backup_freq_var,
                                "value": "monthly",
                                "command": self._apply_backup_freq,
                            },
                        ],
                    },
                    {
                        "kind": "command",
                        "label": "Mentési mappa (gépre)…",
                        "command": self._choose_backup_folder,
                    },
                    {
                        "kind": "command",
                        "label": "Google Drive előkészítés…",
                        "command": self._gdrive_setup_wizard,
                    },
                    {
                        "kind": "command",
                        "label": "Google Drive bejelentkezés…",
                        "command": self._gdrive_login,
                    },
                    {
                        "kind": "command",
                        "label": "Google Drive kijelentkezés",
                        "command": self._gdrive_logout,
                    },
                ],
            ),
            (
                "Súgó",
                [
                    {
                        "kind": "command",
                        "label": "Használati útmutató…",
                        "command": lambda: self._show_help("sugo"),
                    },
                    {
                        "kind": "command",
                        "label": "Mentés és biztonság…",
                        "command": lambda: self._show_help("mentes"),
                    },
                    {
                        "kind": "command",
                        "label": "Google Drive mentés…",
                        "command": lambda: self._show_help("gdrive"),
                    },
                    {
                        "kind": "command",
                        "label": "Adatkezelés…",
                        "command": lambda: self._show_help("adat"),
                    },
                    {"kind": "separator"},
                    {
                        "kind": "command",
                        "label": "Névjegy…",
                        "command": lambda: self._show_help("nevjegy"),
                    },
                ],
            ),
        ]
        bar = CTkMenuBar(self, menus)
        bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        self._menubar = bar

    def _show_help(self, which: str) -> None:
        from app import help_text as ht

        titles = {
            "sugo": "Használati útmutató",
            "mentes": "Mentés és biztonság",
            "gdrive": "Google Drive mentés",
            "adat": "Adatkezelés",
            "nevjegy": "Névjegy",
        }
        bodies = {
            "sugo": ht.SÚGÓ_ROVID,
            "mentes": ht.MENTES_BIZTONSAG,
            "gdrive": ht.GOOGLE_DRIVE_BEJELENTKEZES,
            "adat": ht.ADATKEZELES,
            "nevjegy": ht.NEVJEGY,
        }
        title = titles.get(which, "Súgó")
        body = bodies.get(which, ht.SÚGÓ_ROVID)
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("560x480")
        win.transient(self)
        box = ctk.CTkTextbox(win, wrap="word", font=self._body_font(13))
        box.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        box.insert("1.0", body.strip())
        box.configure(state="disabled")
        ctk.CTkButton(win, text="Bezárás", width=100, command=win.destroy).pack(pady=(0, 12))
        win.after(50, win.lift)

    def _backup_initial_dir(self) -> str:
        cfg = load_config()
        folder = str(cfg.get("backup_folder") or "").strip()
        if folder and Path(folder).is_dir():
            return folder
        return str(Path.home() / "Documents")

    def _apply_backup_target(self) -> None:
        target = str(self._backup_target_var.get() or "local").strip().lower()
        if target not in ("local", "gdrive"):
            target = "local"
            self._backup_target_var.set(target)
        cfg = load_config()
        cfg["backup_target"] = target
        save_config(cfg)
        if target == "gdrive":
            from app.gdrive_backup import is_connected, status_text

            if not is_connected():
                self._set_status(
                    f"Mentés: Google Drive — {status_text()}. Jelentkezz be a menüből.",
                    force=True,
                )
            else:
                self._set_status("Mentés helye: Google Drive", force=True)
        else:
            self._set_status("Mentés helye: gépre (mappa)", force=True)

    def _gdrive_setup_wizard(self) -> None:
        """Egyszeri előkészítés: Google azonosító JSON, utána saját fiókos belépés."""
        import webbrowser

        from app import gdrive_backup as gd

        win = ctk.CTkToplevel(self)
        win.title("Google Drive előkészítés")
        win.geometry("580x520")
        win.transient(self)

        ctk.CTkLabel(
            win,
            text="Google Drive mentés — egyszeri előkészítés",
            font=self._title_font(16),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 6))

        status = ctk.CTkLabel(
            win,
            text=gd.status_text(),
            anchor="w",
            text_color=("gray30", "gray70"),
        )
        status.pack(fill="x", padx=16, pady=(0, 8))

        info = ctk.CTkTextbox(win, wrap="word", height=220, font=self._body_font(13))
        info.pack(fill="both", expand=True, padx=16, pady=4)
        info.insert(
            "1.0",
            "FONTOS: az 1–4. lépéshez VÁLASSZ KI EGY Google-fiókot, és maradj azon.\n"
            "Ne váltogass. (Tipikus: InPrivate / privát ablak, csak azzal a fiókkal.)\n"
            "A gombok fiókválasztót nyitnak — ugyanazt a fiókot kattintsd mindig.\n\n"
            "Ez egyszer kell a programhoz. Utána a mentéshez saját fiókkal belépsz.\n\n"
            "1. Projekt — név pl. HirlevelKoveto → Create.\n"
            "2. Drive API — Enable / Engedélyezés.\n"
            "3. Hozzájárulás — External, app: Hírlevél követő.\n"
            "   Tesztfelhasználó: az a Gmail, amivel majd menteni akarsz.\n"
            "4. Azonosító — OAuth client ID → Desktop app → Download JSON.\n"
            "5. Itt: „Letöltött fájl kiválasztása…”\n"
            "6. „Bejelentkezés…” — azzal a Gmaillel, amit tesztfelhasználónak adtál.\n",
        )
        info.configure(state="disabled")

        def refresh_status() -> None:
            status.configure(text=gd.status_text())

        def open_url(url: str) -> None:
            webbrowser.open(url)

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=6)
        ctk.CTkButton(
            btns, text="1. Projekt", width=100, command=lambda: open_url(gd.URL_PROJECT)
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btns, text="2. Drive API", width=100, command=lambda: open_url(gd.URL_DRIVE_API)
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btns, text="3. Hozzájárulás", width=110, command=lambda: open_url(gd.URL_CONSENT)
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btns, text="4. Azonosító", width=100, command=lambda: open_url(gd.URL_CREDENTIALS)
        ).pack(side="left")

        def pick_json() -> None:
            path = filedialog.askopenfilename(
                title="Google-tól letöltött JSON fájl",
                filetypes=[("JSON", "*.json"), ("Minden", "*.*")],
                initialdir=str(Path.home() / "Downloads"),
            )
            if not path:
                return
            try:
                gd.install_credentials_from_file(path)
                refresh_status()
                messagebox.showinfo(
                    "Google Drive",
                    "Előkészítés kész.\n\nMost: „Bejelentkezés…” — saját Google-fiókkal.",
                )
            except Exception as exc:
                messagebox.showerror("Google Drive", str(exc))

        def do_login() -> None:
            win.destroy()
            self._gdrive_login()

        row2 = ctk.CTkFrame(win, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(4, 14))
        ctk.CTkButton(
            row2, text="5. Letöltött fájl kiválasztása…", command=pick_json
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row2, text="6. Bejelentkezés…", command=do_login).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(row2, text="Bezárás", width=90, command=win.destroy).pack(side="right")
        win.after(50, win.lift)
        refresh_status()

    def _gdrive_login(self) -> None:
        from app import gdrive_backup as gd

        if not gd.credentials_available():
            if messagebox.askyesno(
                "Google Drive",
                "A Drive még nincs előkészítve.\n\n"
                "Megnyitod az előkészítő lépéseket?\n"
                "(Egyszer kell; utána saját fiókkal lehet belépni.)",
            ):
                self._gdrive_setup_wizard()
            return

        def work() -> None:
            try:
                msg = gd.connect_interactive()
                cfg = load_config()
                cfg["backup_target"] = "gdrive"
                save_config(cfg)
                self.after(0, lambda: self._backup_target_var.set("gdrive"))
                self.after(0, lambda: self._set_status(msg, force=True))
                self.after(
                    0,
                    lambda: messagebox.showinfo("Google Drive", msg),
                )
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Google Drive", str(exc)))

        self._set_status("Google Drive bejelentkezés (böngésző)…", force=True)
        threading.Thread(target=work, daemon=True).start()

    def _gdrive_logout(self) -> None:
        try:
            from app.gdrive_backup import disconnect

            disconnect()
            self._set_status("Google Drive: kijelentkezve.", force=True)
        except Exception as exc:
            messagebox.showerror("Google Drive", str(exc))

    def _backup_export(self) -> None:
        cfg = load_config()
        target = str(
            cfg.get("backup_target") or self._backup_target_var.get() or "local"
        ).strip().lower()

        if target == "gdrive":
            def work_gdrive() -> None:
                import tempfile

                try:
                    from app.gdrive_backup import upload_backup_zip

                    with tempfile.TemporaryDirectory(prefix="hirlevel_bak_") as td:
                        path = Path(td) / default_backup_filename()
                        out = create_backup_zip(path)
                        upload_backup_zip(out, keep=int(cfg.get("backup_keep") or 8))
                    cfg2 = load_config()
                    cfg2["backup_last_at"] = datetime.now().isoformat(timespec="seconds")
                    cfg2["backup_target"] = "gdrive"
                    save_config(cfg2)
                    self.after(
                        0,
                        lambda: self._set_status(
                            "Backup a Google Drive-on (HirlevelKoveto-backup).",
                            force=True,
                        ),
                    )
                except Exception as exc:
                    self.after(
                        0,
                        lambda: (
                            self._set_status(f"Backup hiba: {exc}", force=True),
                            messagebox.showerror("Mentés", str(exc)),
                        ),
                    )

            self._set_status("Google Drive mentés…", force=True)
            threading.Thread(target=work_gdrive, daemon=True).start()
            return

        path = filedialog.asksaveasfilename(
            title="Biztonsági másolat mentése a gépre",
            defaultextension=".zip",
            initialdir=self._backup_initial_dir(),
            initialfile=default_backup_filename(),
            filetypes=[("Backup ZIP", "*.zip")],
        )
        if not path:
            return

        def work() -> None:
            try:
                out = create_backup_zip(path)
                cfg2 = load_config()
                cfg2["backup_folder"] = str(Path(out).parent)
                cfg2["backup_last_at"] = datetime.now().isoformat(timespec="seconds")
                cfg2["backup_target"] = "local"
                save_config(cfg2)
                self.after(
                    0,
                    lambda: self._set_status(f"Backup kész: {out}", force=True),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda: messagebox.showerror("Mentés", f"Nem sikerült: {exc}"),
                )

        self._set_status("Backup készítése…", force=True)
        threading.Thread(target=work, daemon=True).start()

    def _backup_restore(self) -> None:
        path = filedialog.askopenfilename(
            title="Backup visszaállítása",
            initialdir=self._backup_initial_dir(),
            filetypes=[("Backup ZIP", "*.zip"), ("Minden", "*.*")],
        )
        if not path:
            return
        ok = messagebox.askyesno(
            "Visszaállítás",
            "A jelenlegi archívum és beállítások felülíródnak "
            "(a program előtte biztonsági másolatot készít a régiről).\n\n"
            "A mentési fájl tartalmazhatja a levelező adataidat is.\n\n"
            "Folytatod?",
        )
        if not ok:
            return
        try:
            restore_backup_zip(path)
            init_db()
            self._reload_sources()
            self._clear_msg_frame()
            self._show_list_empty_state("welcome")
            self._show_reader_placeholder()
            self._set_status(f"Visszaállítva: {path}", force=True)
            messagebox.showinfo(
                "Visszaállítás",
                "Kész. Ha a fiókbeállítások is változtak, indítsd újra az appot.",
            )
        except Exception as exc:
            messagebox.showerror("Visszaállítás", f"Nem sikerült: {exc}")

    def _choose_backup_folder(self) -> None:
        folder = filedialog.askdirectory(
            title="Automata mentés mappája a gépen",
            initialdir=self._backup_initial_dir(),
        )
        if not folder:
            return
        cfg = load_config()
        cfg["backup_folder"] = folder
        cfg["backup_target"] = "local"
        save_config(cfg)
        self._backup_target_var.set("local")
        self._set_status(f"Mentési mappa: {folder}", force=True)
        if self._backup_auto_var.get():
            self.after(500, self._maybe_auto_backup)

    def _apply_backup_auto(self) -> None:
        enabled = bool(self._backup_auto_var.get())
        cfg = load_config()
        target = str(
            self._backup_target_var.get() or cfg.get("backup_target") or "local"
        ).strip().lower()
        if enabled and target != "gdrive":
            folder = str(cfg.get("backup_folder") or "").strip()
            if not folder or not Path(folder).is_dir():
                chosen = filedialog.askdirectory(
                    title="Válassz mentési mappát az automata backuphoz",
                    initialdir=self._backup_initial_dir(),
                )
                if not chosen:
                    self._backup_auto_var.set(False)
                    return
                cfg["backup_folder"] = chosen
        if enabled and target == "gdrive":
            from app.gdrive_backup import is_connected

            if not is_connected():
                messagebox.showinfo(
                    "Automata mentés",
                    "Google Drive célhoz előbb jelentkezz be:\n"
                    "Beállítások → Google Drive bejelentkezés…",
                )
                self._backup_auto_var.set(False)
                return
        cfg["backup_auto"] = enabled
        cfg["backup_target"] = target
        cfg["backup_interval"] = normalize_backup_interval(self._backup_freq_var.get())
        save_config(cfg)
        if enabled:
            where = "Google Drive" if target == "gdrive" else str(cfg.get("backup_folder"))
            self._set_status(
                f"Automata mentés be: {self._backup_freq_label()} → {where}",
                force=True,
            )
            self.after(800, self._maybe_auto_backup)
        else:
            self._set_status("Automata mentés kikapcsolva.", force=True)

    def _apply_backup_freq(self) -> None:
        freq = normalize_backup_interval(self._backup_freq_var.get())
        self._backup_freq_var.set(freq)
        cfg = load_config()
        cfg["backup_interval"] = freq
        save_config(cfg)
        self._set_status(f"Mentés gyakorisága: {self._backup_freq_label()}", force=True)

    def _backup_freq_label(self) -> str:
        return {"daily": "napi", "weekly": "heti", "monthly": "havi"}.get(
            normalize_backup_interval(self._backup_freq_var.get()), "heti"
        )

    def _schedule_backup_check(self) -> None:
        if self._backup_job:
            try:
                self.after_cancel(self._backup_job)
            except Exception:
                pass
            self._backup_job = None

        def tick() -> None:
            self._maybe_auto_backup()
            # Óránként elég ellenőrizni az esedékességet
            self._backup_job = self.after(60 * 60 * 1000, tick)

        # Indítás után rövid késleltetés
        self._backup_job = self.after(12_000, tick)

    def _maybe_auto_backup(self) -> None:
        if self._backup_running or self._syncing:
            return
        cfg = load_config()
        if not backup_due(cfg):
            return
        self._backup_running = True
        self._set_status("Automata biztonsági mentés…", force=True)

        def work() -> None:
            try:
                out = run_scheduled_backup(cfg)
                save_config(cfg)
                self.after(
                    0,
                    lambda: self._set_status(f"Automata backup kész: {out}", force=True),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda: self._set_status(f"Automata backup hiba: {exc}", force=True),
                )
            finally:
                self.after(0, lambda: setattr(self, "_backup_running", False))

        threading.Thread(target=work, daemon=True).start()

    def _apply_interval(self) -> None:
        minutes = int(self._interval_var.get())
        cfg = load_config()
        cfg["check_interval_minutes"] = minutes
        save_config(cfg)
        if self._poll_job:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
            self._poll_job = None
        self._schedule_poll()
        self._set_status(f"Frissítés: {minutes} percenként", force=True)

    def _apply_appearance(self) -> None:
        mode = str(self._appearance_var.get())
        if mode not in ("Light", "Dark"):
            mode = "Dark"
            self._appearance_var.set(mode)
        ctk.set_appearance_mode(mode)
        cfg = load_config()
        cfg["appearance_mode"] = mode
        save_config(cfg)
        # Kényszerített frissítés (néhány CTk widget nem mindig kapja el azonnal)
        try:
            self._menubar.configure(fg_color=("gray85", "gray20"))
        except Exception:
            pass
        label = "világos" if mode == "Light" else "sötét"
        self._set_status(f"Téma: {label}", force=True)
        if self._selected_msg_id is not None:
            self.after(80, lambda: self._show_message_in_reader(self._selected_msg_id))  # type: ignore[arg-type]
        else:
            self.after(80, self._show_reader_placeholder)

    def _apply_autostart(self) -> None:
        want = bool(self._autostart_var.get())
        if want and not is_autostart_enabled():
            enable_autostart()
            self._set_status("Windows indításkor a tálcán indul.", force=True)
        elif not want and is_autostart_enabled():
            disable_autostart()
            self._set_status("Automatikus indítás kikapcsolva.", force=True)
        self._autostart_var.set(is_autostart_enabled())

    def _open_accounts(self) -> None:
        from app.accounts_ui import AccountsWindow

        win = AccountsWindow(
            self, on_saved=lambda: self._set_status(f"Fiókok mentve → {CONFIG_PATH}", force=True)
        )
        win.after(50, win.lift)

    def _add_newsletter(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Hírlevél hozzáadása")
        win.geometry("420x240")
        win.minsize(380, 220)
        win.transient(self)
        win.grab_set()
        win.focus_force()

        ctk.CTkLabel(
            win,
            text="Új hírlevél-forrás (név a listában, e-mail a feladó szűréshez)",
            anchor="w",
            wraplength=380,
        ).pack(fill="x", padx=16, pady=(16, 8))

        form = ctk.CTkFrame(win, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=4)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Név").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        entry_name = ctk.CTkEntry(form, placeholder_text="pl. Knapek Éva")
        entry_name.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form, text="E-mail").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        entry_email = ctk.CTkEntry(form, placeholder_text="pl. info@pelda.hu")
        entry_email.grid(row=1, column=1, sticky="ew", pady=6)

        hint = ctk.CTkLabel(win, text="", anchor="w", text_color=("gray40", "gray70"))
        hint.pack(fill="x", padx=16, pady=(4, 0))

        def save() -> None:
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            if not name:
                hint.configure(text="Add meg a megjelenített nevet.")
                return
            if not email or "@" not in email:
                hint.configure(text="Érvényes e-mail cím kell.")
                return
            if find_source_by_email(email):
                hint.configure(text="Ez az e-mail már szerepel a listában.")
                return
            try:
                new_id = add_source(name, email)
            except Exception as exc:
                hint.configure(text=f"Hiba: {exc}")
                return
            self._reload_sources()
            fresh = get_source(new_id)
            if fresh:
                self._select_source(fresh)
            self._set_status(f"Hírlevél hozzáadva: {name}", force=True)
            win.destroy()

        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=16)
        ctk.CTkButton(row, text="Hozzáadás", command=save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Mégse", command=win.destroy).pack(side="left")
        entry_name.focus_set()

    def _toggle_autostart(self) -> None:
        self._autostart_var.set(not is_autostart_enabled())
        self._apply_autostart()

    def _reload_sources(self, *, reset_scroll: bool = True) -> None:
        counts = count_messages_by_source()
        unread = count_unread_by_source()
        sources = list_sources(active_only=True)
        self._source_names = {s.id: s.name for s in sources}
        self._source_buttons = {}
        self._source_stat_labels = {}
        self._source_name_labels = {}
        for w in self.source_list.winfo_children():
            w.destroy()
        if not sources:
            ctk.CTkLabel(
                self.source_list,
                text="Még nincs hírlevél.\nAdd hozzá a „+ Új hírlevél” gombbal.",
                text_color=("gray40", "gray65"),
                justify="left",
                anchor="w",
            ).pack(anchor="w", padx=8, pady=12)
            if reset_scroll:
                self._reset_scroll(self.source_list)
            return
        selected_id = self._selected.id if self._selected else None
        last_tag: object = object()
        muted = ("gray40", "gray70")
        uj_col = ("#1A56B0", "#6CB6FF")

        for src in sources:
            tag_label = (src.tag or "").strip() or "Egyéb"
            if tag_label != last_tag:
                ctk.CTkLabel(
                    self.source_list,
                    text=tag_label.upper(),
                    font=self._body_font(11),
                    text_color=("gray45", "gray60"),
                    anchor="w",
                    justify="left",
                ).pack(anchor="w", fill="x", padx=10, pady=(10, 2))
                last_tag = tag_label

            n = counts.get(src.id, 0)
            u = unread.get(src.id, 0)
            active = selected_id == src.id
            bg = ("#D5E4F7", "gray30") if active else ("gray85", "gray25")
            hover = ("gray75", "gray35")

            row = ctk.CTkFrame(
                self.source_list,
                fg_color=bg,
                corner_radius=12,
                height=54,
            )
            row.pack(fill="x", pady=3, padx=4)
            row.pack_propagate(False)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=6)

            name_lbl = ctk.CTkLabel(
                inner,
                text=src.name,
                font=self._body_font(13),
                text_color=("gray10", "gray90"),
                anchor="w",
                justify="left",
            )
            name_lbl.pack(fill="x", anchor="w")

            if u:
                stats = f"{n} levél · {u} új"
                stats_color = uj_col
            else:
                stats = f"{n} levél"
                stats_color = muted
            stat_lbl = ctk.CTkLabel(
                inner,
                text=stats,
                font=self._body_font(12),
                text_color=stats_color,
                anchor="w",
                justify="left",
            )
            stat_lbl.pack(fill="x", anchor="w")

            def on_click(_e: object = None, s: Source = src) -> None:
                self._select_source(s)

            def on_enter(_e: object = None, r: ctk.CTkFrame = row, a: bool = active) -> None:
                if not a:
                    try:
                        r.configure(fg_color=hover)
                    except Exception:
                        pass

            def on_leave(_e: object = None, r: ctk.CTkFrame = row, a: bool = active, b=bg) -> None:
                try:
                    r.configure(fg_color=b if a else ("gray85", "gray25"))
                except Exception:
                    pass

            for w in (row, inner, name_lbl, stat_lbl):
                w.bind("<Button-1>", on_click, add="+")
                w.bind("<Enter>", on_enter, add="+")
                w.bind("<Leave>", on_leave, add="+")

            self._source_buttons[src.id] = row
            self._source_name_labels[src.id] = name_lbl
            self._source_stat_labels[src.id] = stat_lbl

        if reset_scroll:
            self._reset_scroll(self.source_list)

    def _refresh_source_badges(self) -> None:
        """Csak szöveg/szín — nem építi újra a bal listát."""
        if not self._source_buttons:
            return
        try:
            counts = count_messages_by_source()
            unread = count_unread_by_source()
        except Exception:
            return
        selected_id = self._selected.id if self._selected else None
        muted = ("gray40", "gray70")
        uj_col = ("#1A56B0", "#6CB6FF")
        for sid, row in list(self._source_buttons.items()):
            try:
                if not row.winfo_exists():
                    continue
            except Exception:
                continue
            name = self._source_names.get(sid, "")
            n = counts.get(sid, 0)
            u = unread.get(sid, 0)
            active = selected_id == sid
            bg = ("#D5E4F7", "gray30") if active else ("gray85", "gray25")
            if u:
                stats = f"{n} levél · {u} új"
                stats_color = uj_col
            else:
                stats = f"{n} levél"
                stats_color = muted
            try:
                row.configure(fg_color=bg)
                nl = self._source_name_labels.get(sid)
                sl = self._source_stat_labels.get(sid)
                if nl is not None:
                    nl.configure(text=name)
                if sl is not None:
                    sl.configure(text=stats, text_color=stats_color)
            except Exception:
                pass

    def _schedule_badge_refresh(self) -> None:
        if self._source_badge_job is not None:
            try:
                self.after_cancel(self._source_badge_job)
            except Exception:
                pass
        self._source_badge_job = self.after(120, self._do_badge_refresh)

    def _do_badge_refresh(self) -> None:
        self._source_badge_job = None
        self._refresh_source_badges()

    def _select_source(self, src: Source) -> None:
        self._selected = src
        self._global_results = False
        self._reader_focus = False
        if self._compact:
            self._apply_layout_mode()
        self.header.configure(text=src.name)
        self._clear_find()
        if self.search.get().strip():
            self.search.delete(0, "end")
        # Ne jelöljük automatikusan olvasottnak — maradjon látható az ÚJ
        self._refresh_source_badges()
        self._reload_messages(browse_source=True)

    def _run_search(self) -> None:
        q = self.search.get().strip()
        if not q:
            messagebox.showinfo("Keresés", "Írj be keresőszót.")
            return
        if self.search_only_selected_var.get() and not self._selected:
            messagebox.showinfo(
                "Keresés",
                "A „Csak a kiválasztottban” be van pipálva — válassz hírlevelet bal oldalon, "
                "vagy kapcsold ki a pipát a teljes kereséshez.",
            )
            return
        self._global_results = not self.search_only_selected_var.get()
        self._reload_messages(browse_source=False)

    def _clear_search(self) -> None:
        self.search.delete(0, "end")
        self._global_results = False
        self._clear_find()
        if self._selected:
            self.header.configure(text=self._selected.name)
            self._reload_messages(browse_source=True)
        else:
            self.header.configure(text="Hírlevél követő")
            self._clear_msg_frame()
            self._show_list_empty_state("welcome")
            self._set_status("", force=True)

    def _rename_selected(self) -> None:
        if not self._selected:
            messagebox.showinfo("Átnevezés", "Előbb válassz egy hírlevelet a bal oldalon.")
            return

        dialog = ctk.CTkInputDialog(
            text=f"Új név — jelenleg: {self._selected.name}",
            title="Hírlevél átnevezése",
        )
        new_name = dialog.get_input()
        if new_name is None:
            return
        new_name = new_name.strip()
        if not new_name:
            messagebox.showwarning("Átnevezés", "A név nem lehet üres.")
            return
        if new_name == self._selected.name:
            return

        if not rename_source(self._selected.id, new_name):
            messagebox.showerror("Átnevezés", "Nem sikerült átnevezni.")
            return

        fresh = get_source(self._selected.id)
        if fresh:
            self._selected = fresh
            self.header.configure(text=fresh.name)
        self._reload_sources()
        self._set_status(f"Átnevezve: {new_name}")

    def _list_filter_kwargs(self) -> dict:
        mode = str(self._filter_var.get() if hasattr(self, "_filter_var") else "all")
        since = ""
        if hasattr(self, "since_entry"):
            since = self.since_entry.get().strip()
            if since and not re.match(r"^\d{4}-\d{2}-\d{2}", since):
                since = ""
        return {
            "unread_only": mode == "unread",
            "starred_only": mode == "starred",
            "since_date": since,
        }

    def _apply_list_filter(self) -> None:
        since = self.since_entry.get().strip() if hasattr(self, "since_entry") else ""
        if since and not re.match(r"^\d{4}-\d{2}-\d{2}", since):
            messagebox.showinfo("Szűrő", "A dátum formátuma: ÉÉÉÉ-HH-NN (pl. 2026-07-01).")
            return
        if self.search.get().strip() and not self._selected:
            self._reload_messages(browse_source=False)
        elif self._selected:
            self._reload_messages(browse_source=not bool(self.search.get().strip()))
        else:
            messagebox.showinfo("Szűrő", "Válassz hírlevelet, vagy keress előbb.")

    def _tag_selected(self) -> None:
        if not self._selected:
            messagebox.showinfo("Címke", "Előbb válassz egy hírlevelet.")
            return
        dialog = ctk.CTkInputDialog(
            text=f"Címke (üres = törlés) — most: {self._selected.tag or '—'}",
            title="Hírlevél címke",
        )
        raw = dialog.get_input()
        if raw is None:
            return
        tag = raw.strip()
        if not set_source_tag(self._selected.id, tag):
            messagebox.showerror("Címke", "Nem sikerült menteni.")
            return
        fresh = get_source(self._selected.id)
        if fresh:
            self._selected = fresh
        self._reload_sources()
        self._set_status(f"Címke: {tag or '(nincs)'}", force=True)

    def _mark_selected_all_read(self) -> None:
        if not self._selected:
            messagebox.showinfo(
                "Olvasott",
                "Előbb válassz egy hírlevelet a bal oldalon.",
            )
            return
        try:
            n = mark_source_messages_read(self._selected.id)
        except Exception as exc:
            messagebox.showerror("Olvasott", str(exc))
            return
        for m in list(self._messages_cache):
            if m.source_id == self._selected.id and not m.is_read:
                self._update_cached_message(m.id, is_read=1)
        self._refresh_source_badges()
        if hasattr(self, "_filter_var") and self._filter_var.get() == "unread":
            self._reload_messages(browse_source=True)
        else:
            self._rerender_bubbles()
        self._set_status(
            f"{n} olvasatlan → olvasott: {self._selected.name}"
            if n
            else f"Nincs olvasatlan: {self._selected.name}",
            force=True,
        )

    def _mark_everything_read(self) -> None:
        if not messagebox.askyesno(
            "Olvasott",
            "Minden hírlevél minden olvasatlan levelét olvasottnak jelölöd?",
        ):
            return
        try:
            n = mark_all_messages_read()
        except Exception as exc:
            messagebox.showerror("Olvasott", str(exc))
            return
        for m in list(self._messages_cache):
            if not m.is_read:
                self._update_cached_message(m.id, is_read=1)
        self._refresh_source_badges()
        if hasattr(self, "_filter_var") and self._filter_var.get() == "unread":
            self._reload_messages(browse_source=bool(self._selected))
        else:
            self._rerender_bubbles()
        self._set_status(
            f"Minden olvasatlan olvasott: {n} levél" if n else "Nem volt olvasatlan levél.",
            force=True,
        )

    def _hide_selected(self) -> None:
        if not self._selected:
            messagebox.showinfo("Elrejtés", "Előbb válassz egy hírlevelet.")
            return
        name = self._selected.name
        if not messagebox.askyesno(
            "Elrejtés",
            f"Elrejted: {name}?\n(Nem törlődik; az „Elrejtettek…” menüből visszaállítható.)",
        ):
            return
        set_source_active(self._selected.id, False)
        self._selected = None
        self.header.configure(text="Hírlevél követő")
        self._clear_msg_frame()
        self._show_list_empty_state("welcome")
        self._reload_sources()
        self._set_status(f"Elrejtve: {name}", force=True)

    def _manage_hidden_sources(self) -> None:
        hidden = [s for s in list_sources(active_only=False) if not s.active]
        if not hidden:
            messagebox.showinfo("Elrejtettek", "Nincs elrejtett hírlevél.")
            return
        win = ctk.CTkToplevel(self)
        win.title("Elrejtett hírlevelek")
        win.geometry("420x360")
        win.transient(self)
        ctk.CTkLabel(win, text="Visszaállítás a listába:", font=self._title_font(15)).pack(
            anchor="w", padx=14, pady=(14, 8)
        )
        box = ctk.CTkScrollableFrame(win)
        box.pack(fill="both", expand=True, padx=12, pady=4)

        def restore(sid: int, w=win) -> None:
            set_source_active(sid, True)
            self._reload_sources()
            self._set_status("Hírlevél visszaállítva.", force=True)
            w.destroy()

        for src in hidden:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=src.name, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="Vissza", width=80, command=lambda i=src.id: restore(i)
            ).pack(side="right")

        ctk.CTkButton(win, text="Bezárás", command=win.destroy).pack(pady=10)

    def _reload_messages(self, *, browse_source: bool = False) -> None:
        self._render_token += 1
        token = self._render_token
        self._clear_msg_frame()
        self._messages_cache = []
        self._shown_count = 0
        self._last_day = ""
        self._day_index = -1

        q = self.search.get().strip()
        source_id: Optional[int] = None
        global_view = False

        if browse_source:
            # Forrás böngészésekor mindig az összes levél — ne a keresőszűrő
            q = ""
            if not self._selected:
                self._show_list_empty_state("no_source")
                return
            source_id = self._selected.id
            fresh = get_source(self._selected.id)
            if fresh:
                self._selected = fresh
                self.header.configure(text=fresh.name)
            self._global_results = False
        else:
            only_selected = self.search_only_selected_var.get()
            if only_selected:
                if not self._selected:
                    self._show_list_empty_state("no_source")
                    return
                source_id = self._selected.id
                self.header.configure(text=f"Keresés — {self._selected.name}: „{q}”")
            else:
                global_view = True
                self._global_results = True
                self.header.configure(text=f"Keresés: „{q}”")

        ctk.CTkLabel(self.msg_frame, text="Betöltés…", text_color=("gray40", "gray70")).pack(
            anchor="w", pady=8, padx=12
        )
        self.update_idletasks()

        def load() -> None:
            try:
                flt = self._list_filter_kwargs()
                msgs = list_messages(
                    source_id=source_id,
                    query=q,
                    limit=LIST_FETCH_LIMIT,
                    **flt,
                )
            except Exception as exc:
                self.after(0, lambda: self._set_status(f"Betöltési hiba: {exc}"))
                return

            def start_render() -> None:
                if token != self._render_token:
                    return
                self._clear_msg_frame()
                self._messages_cache = msgs
                self._global_results = global_view or (
                    not browse_source and not self.search_only_selected_var.get() and bool(q)
                )
                if not msgs:
                    self._clear_find()
                    self._show_list_empty_state(
                        "no_mail" if browse_source or not q else "empty_search"
                    )
                    return
                width = self.msg_frame.winfo_width()
                self._wrap = max(280, min(width - 40, 520)) if width > 80 else 360
                self._suppress_auto_open = bool(q) and not browse_source
                self._shown_count = 0
                self._last_day = ""
                self._day_index = -1
                try:
                    self._reset_scroll(self.msg_frame)
                except Exception:
                    pass
                self._render_next_page(token)
                if q and not browse_source:
                    self._find_query = q
                    self._find_hits = self._collect_find_hits(msgs, q)
                    self._find_index = 0 if self._find_hits else -1
                    self._update_find_nav()
                    if self._find_hits:
                        letters = len({h["msg_id"] for h in self._find_hits})
                        self._set_status(
                            f"{len(self._find_hits)} találat {letters} levélben — „{q}”",
                            force=True,
                        )
                        self.after(120, self._goto_find_hit)
                    else:
                        self._set_status(f"Nincs szöveges előfordulás: „{q}”", force=True)
                else:
                    self._clear_find()

            self.after(0, start_render)

        threading.Thread(target=load, daemon=True).start()

    def _render_next_page(self, token: int) -> None:
        """Következő max PAGE_SIZE buborék a görgethető listába + Több betöltése."""
        if token != self._render_token:
            return
        if not self._messages_cache:
            return

        bubble = ("#E4E8EE", "#252A32")
        bubble_unread = ("#E8F0FC", "#3A4A5E")
        bubble_sel = ("#C9DBF2", "#3A4554")
        day_bar = ("#C5D0DC", "#252A32")
        day_text = ("gray10", "gray90")
        muted = ("gray40", "gray70")
        text_col = ("gray10", "#F0F2F5")
        accent = ("#2F6FED", "#6CB6FF")
        uj_bg = ("#2F6FED", "#3D7FE0")
        uj_fg = ("#FFFFFF", "#FFFFFF")

        for w in self.msg_frame.winfo_children():
            if getattr(w, "_is_more_btn", False):
                w.destroy()

        end = min(self._shown_count + PAGE_SIZE, len(self._messages_cache))
        batch = self._messages_cache[self._shown_count : end]

        for msg in batch:
            day_key, day_label, time_label = self._split_when(msg.received_at)
            if day_key != self._last_day:
                self._last_day = day_key
                self._day_index += 1
                header = ctk.CTkFrame(
                    self.msg_frame, fg_color=day_bar, corner_radius=8, height=34
                )
                header.pack(fill="x", pady=(14 if self._day_index else 4, 8), padx=8)
                header.pack_propagate(False)
                ctk.CTkLabel(
                    header,
                    text=f"  {day_label}",
                    font=self._title_font(13),
                    text_color=day_text,
                    anchor="w",
                ).pack(side="left", fill="y", padx=8)

            selected = self._selected_msg_id == msg.id
            unread = int(getattr(msg, "is_read", 1) or 0) == 0
            if selected:
                bg = bubble_sel
            elif unread:
                bg = bubble_unread
            else:
                bg = bubble
            card = ctk.CTkFrame(
                self.msg_frame,
                fg_color=bg,
                corner_radius=16,
                border_width=3 if unread else (2 if selected else 1),
                border_color=accent
                if (unread or selected)
                else ("#D0D8E2", "#3A404A"),
            )
            card._msg_id = int(msg.id)  # type: ignore[attr-defined]
            card.pack(fill="x", pady=(0, 10), padx=(12, 20))

            meta = ctk.CTkFrame(card, fg_color="transparent")
            meta.pack(fill="x", padx=14, pady=(10, 0))
            left_meta = ctk.CTkFrame(meta, fg_color="transparent")
            left_meta.pack(side="left")
            if unread:
                uj = ctk.CTkFrame(left_meta, fg_color=uj_bg, corner_radius=6)
                uj._is_uj_badge = True  # type: ignore[attr-defined]
                uj.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(
                    uj,
                    text="ÚJ",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=uj_fg,
                ).pack(padx=7, pady=2)
            ctk.CTkLabel(
                left_meta,
                text=time_label,
                font=ctk.CTkFont(size=12, weight="bold" if unread else "normal"),
                text_color=accent if unread else muted,
            ).pack(side="left")
            if self._global_results:
                src_name = self._source_names.get(msg.source_id, "Hírlevél")
                ctk.CTkLabel(
                    meta,
                    text=src_name,
                    font=self._body_font(12),
                    text_color=muted,
                ).pack(side="right")

            subj_text = msg.subject
            if msg.is_starred:
                subj_text = f"★ {subj_text}"
            subj = ctk.CTkLabel(
                card,
                text=subj_text,
                font=ctk.CTkFont(
                    family="Candara",
                    size=15,
                    weight="bold" if unread or selected else "normal",
                ),
                text_color=text_col if (unread or selected) else muted,
                wraplength=self._wrap,
                justify="left",
                anchor="w",
            )
            subj.pack(anchor="w", padx=14, pady=(6, 4))

            preview, has_more = self._bubble_preview(msg.body_text or "")
            prev = ctk.CTkLabel(
                card,
                text=preview,
                font=self._body_font(13),
                text_color=muted,
                wraplength=self._wrap,
                justify="left",
                anchor="w",
            )
            prev.pack(anchor="w", padx=14, pady=(0, 4))

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=10, pady=(2, 10))

            def _open_full(mid: int = msg.id) -> None:
                mid = int(mid)
                if self._find_hits and self._find_query:
                    for i, h in enumerate(self._find_hits):
                        if int(h["msg_id"]) == mid:
                            self._find_index = i
                            self._goto_find_hit()
                            return
                self._show_message_in_reader(mid)
                self._set_status("Teljes szöveg a jobb oldali olvasóban.", force=True)

            open_btn = ctk.CTkButton(
                actions,
                text="Teljes szöveg",
                width=120,
                height=30,
                corner_radius=14,
                fg_color=("#B8C9DE", "gray35"),
                hover_color=("#A5B8D0", "#5A6878"),
                text_color=text_col,
                command=_open_full,
            )
            open_btn.pack(side="left", padx=(0, 6))

            star_btn = ctk.CTkButton(
                actions,
                text="★" if msg.is_starred else "☆",
                width=36,
                height=30,
                corner_radius=12,
                fg_color=("gray85", "gray30"),
                hover_color=("#E8D48A", "#5A5040"),
                text_color=("#B8860B", "#FFD54F") if msg.is_starred else text_col,
                command=lambda mid=msg.id: self._toggle_star(mid),
            )
            star_btn.pack(side="left", padx=(0, 6))

            pdf_btn = ctk.CTkButton(
                actions,
                text="PDF",
                width=48,
                height=30,
                corner_radius=12,
                fg_color=("gray85", "gray30"),
                hover_color=("#A5B8D0", "#5A6878"),
                text_color=text_col,
                command=lambda mid=msg.id: self._export_one(mid, "pdf"),
            )
            pdf_btn.pack(side="left", padx=(0, 6))

            word_btn = ctk.CTkButton(
                actions,
                text="Word",
                width=56,
                height=30,
                corner_radius=12,
                fg_color=("gray85", "gray30"),
                hover_color=("#A5B8D0", "#5A6878"),
                text_color=text_col,
                command=lambda mid=msg.id: self._export_one(mid, "docx"),
            )
            word_btn.pack(side="left", padx=(0, 6))

            copy_btn = ctk.CTkButton(
                actions,
                text="Másolat",
                width=72,
                height=30,
                corner_radius=12,
                fg_color=("gray85", "gray30"),
                hover_color=("#A5B8D0", "#5A6878"),
                text_color=text_col,
                command=lambda mid=msg.id: self._copy_message(mid),
            )
            copy_btn.pack(side="left")

            def _click(_event: object = None, mid: int = msg.id) -> None:
                _open_full(mid)

            # Csak a kártya „tartalom” része nyit — a gombok saját command-je él
            for w in (meta, left_meta, subj, prev):
                try:
                    w.bind("<Button-1>", lambda _e, m=msg.id: _open_full(m), add="+")
                except Exception:
                    pass
            try:
                card.bind("<Button-1>", lambda _e, m=msg.id: _open_full(m), add="+")
            except Exception:
                pass

        self._shown_count = end

        if self._shown_count < len(self._messages_cache):
            more = ctk.CTkButton(
                self.msg_frame,
                text=f"Több betöltése ({self._shown_count}/{len(self._messages_cache)})",
                command=lambda: self._render_next_page(token),
            )
            more._is_more_btn = True  # type: ignore[attr-defined]
            more.pack(fill="x", pady=10, padx=4)

        if self._global_results:
            scope = "összes forrás"
        else:
            scope = self._selected.name if self._selected else ""
        self._set_status(
            f"{self._shown_count}/{len(self._messages_cache)} megjelenítve — {scope}",
            force=True,
        )
        try:
            self.msg_frame.update_idletasks()
            canvas = self.msg_frame._parent_canvas  # noqa: SLF001
            bbox = canvas.bbox("all")
            canvas.configure(scrollregion=bbox if bbox else (0, 0, 0, 0))
        except Exception:
            pass
        if (
            self._shown_count
            and self._selected_msg_id is None
            and self._shown_count <= PAGE_SIZE
            and not self._suppress_auto_open
            and not self._compact
        ):
            first_id = self._messages_cache[0].id
            self.after(250, lambda mid=first_id: self._show_message_in_reader(mid))

    def _add_body_with_links(self, parent: ctk.CTkFrame, text: str, *, bg: tuple[str, str]) -> None:
        """Szöveg + kattintható http(s) / www linkek."""
        width = max(400, min(self._wrap, 900))
        box = ctk.CTkTextbox(
            parent,
            width=width,
            height=60,
            fg_color=bg,
            text_color=("gray20", "gray85"),
            border_width=0,
            activate_scrollbars=False,
            wrap="word",
            font=ctk.CTkFont(size=13),
        )
        box.pack(anchor="w", fill="x", padx=14, pady=(0, 14))

        inner: tk.Text = box._textbox  # noqa: SLF001 — link tagekhez kell
        inner.configure(cursor="arrow", padx=0, pady=0)
        inner.tag_configure("link", foreground="#6CB6FF", underline=True)

        def _clean_url(raw: str) -> str:
            url = raw.rstrip(".,;:!?)]}>\"'")
            if url.lower().startswith("www."):
                url = "https://" + url
            return url

        def _on_link_click(event: tk.Event) -> str:  # type: ignore[type-arg]
            index = inner.index(f"@{event.x},{event.y}")
            tags = inner.tag_names(index)
            for tag in tags:
                if tag.startswith("url:"):
                    webbrowser.open(tag[4:])
                    break
            return "break"

        inner.tag_bind("link", "<Button-1>", _on_link_click)
        inner.tag_bind("link", "<Enter>", lambda _e: inner.configure(cursor="hand2"))
        inner.tag_bind("link", "<Leave>", lambda _e: inner.configure(cursor="arrow"))

        box.configure(state="normal")
        inner.delete("1.0", "end")
        pos = 0
        for match in URL_RE.finditer(text):
            start, end = match.span()
            if start > pos:
                inner.insert("end", text[pos:start])
            raw_url = match.group(0)
            url = _clean_url(raw_url)
            tag_name = f"url:{url}"
            inner.insert("end", raw_url, ("link", tag_name))
            pos = end
        if pos < len(text):
            inner.insert("end", text[pos:])
        if not text:
            inner.insert("end", "(nincs szöveges törzs)")

        # Magasság a sorokhoz igazítva (max ~12 sor a listában)
        inner.update_idletasks()
        line_count = int(float(inner.index("end-1c").split(".")[0]))
        line_count = max(2, min(line_count + 1, 12))
        box.configure(height=line_count * 18 + 8)
        box.configure(state="disabled")

        # Disabled Text / CTkTextbox elnyeli a görgőt — továbbítjuk a listának
        for target in (box, inner):
            target.bind("<MouseWheel>", self._scroll_messages)
            if "linux" in sys.platform:
                target.bind("<Button-4>", self._scroll_messages)
                target.bind("<Button-5>", self._scroll_messages)

    @staticmethod
    def _split_when(received_at: str) -> tuple[str, str, str]:
        raw = (received_at or "").replace("T", " ").strip()
        day_key = raw[:10] if len(raw) >= 10 else raw
        time_label = raw[11:16] if len(raw) >= 16 else ""
        try:
            dt = datetime.strptime(day_key, "%Y-%m-%d")
            ma = datetime.now().date()
            d = dt.date()
            if d == ma:
                day_label = f"Ma — {dt:%Y. %m. %d.}"
            elif d == ma.fromordinal(ma.toordinal() - 1):
                day_label = f"Tegnap — {dt:%Y. %m. %d.}"
            else:
                weekdays = (
                    "hétfő",
                    "kedd",
                    "szerda",
                    "csütörtök",
                    "péntek",
                    "szombat",
                    "vasárnap",
                )
                day_label = f"{weekdays[dt.weekday()]} — {dt:%Y. %m. %d.}"
        except ValueError:
            day_label = day_key or "Ismeretlen nap"
        return day_key, day_label, time_label or "—"

    def _update_cached_message(self, msg_id: int, **kwargs: object) -> None:
        for i, m in enumerate(self._messages_cache):
            if m.id == msg_id:
                data = {
                    "id": m.id,
                    "source_id": m.source_id,
                    "account_id": m.account_id,
                    "gmail_uid": m.gmail_uid,
                    "subject": m.subject,
                    "body_text": m.body_text,
                    "received_at": m.received_at,
                    "created_at": m.created_at,
                    "body_html": m.body_html,
                    "is_read": m.is_read,
                    "is_starred": m.is_starred,
                }
                data.update(kwargs)
                self._messages_cache[i] = Message(**data)  # type: ignore[arg-type]
                break

    def _mark_message_read(self, msg_id: int) -> None:
        msg_id = int(msg_id)
        was_unread = False
        for m in self._messages_cache:
            if int(m.id) == msg_id and int(getattr(m, "is_read", 1) or 0) == 0:
                was_unread = True
                break
        try:
            set_message_read(msg_id, True)
        except Exception as exc:
            self._set_status(f"Olvasott jelölés hiba: {exc}", force=True)
            return
        self._update_cached_message(msg_id, is_read=1)
        self._schedule_badge_refresh()
        # Ne építsük újra a listát (üres óriás buborék / ugrás) — helyben frissítünk
        if was_unread or self._selected_msg_id == msg_id:
            self._apply_bubble_styles(remove_uj_for=msg_id if was_unread else None)

    def _apply_bubble_styles(self, *, remove_uj_for: Optional[int] = None) -> None:
        """Kijelölés / olvasott kinézet újrarajzolás nélkül."""
        bubble = ("#E4E8EE", "#252A32")
        bubble_unread = ("#E8F0FC", "#3A4A5E")
        bubble_sel = ("#C9DBF2", "#3A4554")
        accent = ("#2F6FED", "#6CB6FF")
        for w in self.msg_frame.winfo_children():
            mid = getattr(w, "_msg_id", None)
            if mid is None:
                continue
            msg = next((m for m in self._messages_cache if int(m.id) == int(mid)), None)
            if msg is None:
                continue
            selected = self._selected_msg_id == int(mid)
            unread = int(getattr(msg, "is_read", 1) or 0) == 0
            if selected:
                bg = bubble_sel
            elif unread:
                bg = bubble_unread
            else:
                bg = bubble
            try:
                w.configure(
                    fg_color=bg,
                    border_width=3 if unread else (2 if selected else 1),
                    border_color=accent
                    if (unread or selected)
                    else ("#D0D8E2", "#3A404A"),
                )
            except Exception:
                continue
            if remove_uj_for is not None and int(mid) == int(remove_uj_for):
                try:
                    for ch in list(w.winfo_children()):
                        self._destroy_uj_badges(ch)
                except Exception:
                    pass

    def _destroy_uj_badges(self, widget: object) -> None:
        try:
            if getattr(widget, "_is_uj_badge", False):
                widget.destroy()  # type: ignore[attr-defined]
                return
        except Exception:
            return
        try:
            for ch in list(widget.winfo_children()):  # type: ignore[attr-defined]
                self._destroy_uj_badges(ch)
        except Exception:
            pass

    def _schedule_bubble_refresh(self) -> None:
        job = getattr(self, "_bubble_refresh_job", None)
        if job is not None:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._bubble_refresh_job = self.after(60, self._do_bubble_refresh)

    def _do_bubble_refresh(self) -> None:
        self._bubble_refresh_job = None
        pos = 0.0
        try:
            pos = float(self.msg_frame._parent_canvas.yview()[0])  # noqa: SLF001
        except Exception:
            pass
        self._rerender_bubbles()
        try:
            self.msg_frame._parent_canvas.yview_moveto(pos)  # noqa: SLF001
        except Exception:
            pass

    def _toggle_star(self, msg_id: int) -> None:
        try:
            starred = toggle_message_starred(msg_id)
        except Exception as exc:
            self._set_status(f"Kedvenc hiba: {exc}", force=True)
            return
        self._update_cached_message(msg_id, is_starred=1 if starred else 0)
        self._set_status("Kedvenchez adva." if starred else "Kedvenc törölve.", force=True)
        if hasattr(self, "_filter_var") and self._filter_var.get() == "starred" and not starred:
            self._messages_cache = [m for m in self._messages_cache if m.id != msg_id]
        self._schedule_bubble_refresh()

    def _copy_message(self, msg_id: int) -> None:
        msg = next((m for m in self._messages_cache if m.id == msg_id), None)
        if msg is None:
            msg = get_message(msg_id)
        if msg is None:
            return
        full = get_message(msg_id) or msg
        links = self._extract_links(full.body_html or "", full.body_text or "")
        parts = [
            full.subject or "(nincs tárgy)",
            (full.received_at or "").replace("T", " "),
            "",
            (full.body_text or "").strip(),
        ]
        if links:
            parts.extend(["", "Linkek:", *links])
        text = "\n".join(parts).strip()
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update_idletasks()
            self._set_status("Másolva a vágólapra.", force=True)
        except Exception as exc:
            messagebox.showerror("Másolat", str(exc))

    @staticmethod
    def _extract_links(html: str, plain: str = "") -> list[str]:
        found: list[str] = []
        seen: set[str] = set()
        if html.strip():
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = str(a.get("href") or "").strip()
                    if not href or href.startswith("#") or href.lower().startswith("mailto:"):
                        continue
                    if href not in seen:
                        seen.add(href)
                        found.append(href)
            except Exception:
                pass
        for match in URL_RE.finditer(plain or ""):
            url = match.group(0)
            while url and url[-1] in ".,;:!?)]}>\"'":
                url = url[:-1]
            if url.lower().startswith("www."):
                url = "https://" + url
            if url and url not in seen:
                seen.add(url)
                found.append(url)
        return found

    def _show_reader_links(self) -> None:
        msg_id = self._selected_msg_id
        if msg_id is None:
            messagebox.showinfo("Linkek", "Előbb nyiss meg egy levelet.")
            return
        full = get_message(int(msg_id))
        if not full:
            return
        links = self._extract_links(full.body_html or "", full.body_text or "")
        if not links:
            messagebox.showinfo("Linkek", "Nincs link ebben a levélben.")
            return
        win = ctk.CTkToplevel(self)
        win.title("Linkek a levélben")
        win.geometry("560x420")
        win.transient(self)
        ctk.CTkLabel(
            win, text=full.subject or "Linkek", font=self._title_font(15), anchor="w"
        ).pack(fill="x", padx=14, pady=(12, 6))
        box = ctk.CTkScrollableFrame(win)
        box.pack(fill="both", expand=True, padx=12, pady=4)

        def open_url(u: str) -> None:
            webbrowser.open(u)

        def copy_url(u: str) -> None:
            self.clipboard_clear()
            self.clipboard_append(u)
            self._set_status("Link másolva.", force=True)

        for url in links:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=url, anchor="w", wraplength=360, justify="left").pack(
                side="left", fill="x", expand=True
            )
            ctk.CTkButton(row, text="Nyit", width=56, command=lambda u=url: open_url(u)).pack(
                side="right", padx=(4, 0)
            )
            ctk.CTkButton(row, text="Másol", width=64, command=lambda u=url: copy_url(u)).pack(
                side="right"
            )

        def copy_all() -> None:
            self.clipboard_clear()
            self.clipboard_append("\n".join(links))
            self._set_status("Összes link másolva.", force=True)

        bar = ctk.CTkFrame(win, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=10)
        ctk.CTkButton(bar, text="Összes másolása", command=copy_all).pack(side="left")
        ctk.CTkButton(bar, text="Bezárás", command=win.destroy).pack(side="right")

    def _rerender_bubbles(self) -> None:
        keep = max(self._shown_count, PAGE_SIZE)
        self._shown_count = 0
        self._last_day = ""
        self._day_index = -1
        for w in self.msg_frame.winfo_children():
            w.destroy()
        self._render_token += 1
        token = self._render_token
        while self._shown_count < min(keep, len(self._messages_cache)):
            self._render_next_page(token)

    @staticmethod
    def _export_filename_stem(
        title: str,
        *,
        when: str = "",
        source_name: str = "",
        max_len: int = 100,
    ) -> str:
        """forrás - Cím - dátum"""
        return export_filename_stem(
            source_name or "hirlevel",
            title,
            when=when,
            max_len=max_len,
        )

    def _export_current(self, kind: str = "docx") -> None:
        if self._selected_msg_id is None:
            messagebox.showinfo("Export", "Előbb nyiss meg egy levelet az olvasóban.")
            return
        self._export_one(int(self._selected_msg_id), kind)

    def _export_one(self, msg_id: int, kind: str = "docx") -> None:
        kind = "pdf" if kind == "pdf" else "docx"
        msg = next((m for m in self._messages_cache if m.id == msg_id), None)
        if msg is None:
            msg = get_message(msg_id)
        if msg is None:
            messagebox.showinfo("Export", "Nem található a levél.")
            return
        src = get_source(msg.source_id)
        stem = self._export_filename_stem(
            msg.subject or "level",
            when=msg.received_at or "",
            source_name=(src.name if src else "") or "hirlevel",
        )
        if kind == "pdf":
            path = filedialog.asksaveasfilename(
                title="Levél PDF mentése (HTML nézet)",
                defaultextension=".pdf",
                initialfile=f"{stem}.pdf",
                filetypes=[("PDF", "*.pdf")],
            )
        else:
            path = filedialog.asksaveasfilename(
                title="Levél Word mentése (HTML nézet)",
                defaultextension=".docx",
                initialfile=f"{stem}.docx",
                filetypes=[("Word", "*.docx")],
            )
        if not path:
            return

        # Ha az olvasóban van: a megjelenített HTML; különben ugyanazt építjük a DB HTML-ből
        open_reader_html = ""
        if self._selected_msg_id == msg_id:
            rh = (self._last_reader_html or "").strip()
            if rh and "Válassz egy levelet" not in rh and ">Betöltés" not in rh:
                open_reader_html = rh

        def work() -> None:
            try:
                full = get_message(msg_id) or msg
                needs_html = _is_stub_message(
                    full.body_text or "", full.body_html or ""
                ) or not (full.body_html or "").strip()
                if needs_html:
                    try:
                        if refresh_one_message_html(msg_id):
                            full = get_message(msg_id) or full
                    except Exception:
                        pass

                if open_reader_html:
                    html_out = open_reader_html
                else:
                    raw = (full.body_html or "").strip()
                    if not raw:
                        raw = self._plain_text_to_linked_html(
                            full.body_text or "(nincs tartalom)"
                        )
                    html_out = self._wrap_reader_html(raw)

                if kind == "pdf":
                    export_message_to_pdf(path, full, source=src, html=html_out)
                else:
                    export_message_to_docx(path, full, source=src, html=html_out)
                self.after(0, lambda: self._set_status(f"Export kész: {path}", force=True))
            except Exception as exc:
                self.after(
                    0,
                    lambda: (
                        self._set_status(f"Export hiba: {exc}", force=True),
                        messagebox.showerror("Export", str(exc)),
                    ),
                )

        self._set_status(
            "PDF export folyamatban…" if kind == "pdf" else "Word export folyamatban…",
            force=True,
        )
        threading.Thread(target=work, daemon=True).start()

    def _export(self) -> None:
        """Aktuális (szűrt) lista → egy Word fájl."""
        messages = list(self._messages_cache)
        if not messages:
            messagebox.showinfo("Export", "Nincs exportálható levél a listában.")
            return
        if self._selected and not self._global_results:
            src = self._selected
            title = src.name
            stem = self._export_filename_stem(
                "Lista",
                when=datetime.now().isoformat(),
                source_name=src.name,
            )
        else:
            src = None
            q = self.search.get().strip()
            title = "Összes hírlevél" if not q else f"Keresés: {q}"
            stem = self._export_filename_stem(
                q or "Lista",
                when=datetime.now().isoformat(),
                source_name="Összes" if not q else "Keresés",
            )
        path = filedialog.asksaveasfilename(
            title="Lista Word mentése",
            defaultextension=".docx",
            initialfile=f"{stem}.docx",
            filetypes=[("Word", "*.docx")],
        )
        if not path:
            return

        def work() -> None:
            try:
                # Teljes HTML-hez újratöltés id-k alapján
                fulls = []
                for m in messages[:500]:
                    fulls.append(get_message(m.id) or m)
                export_messages_to_docx(
                    path,
                    source=src,
                    messages=fulls,
                    title=title,
                )
                self.after(0, lambda: self._set_status(f"Export kész: {path}", force=True))
            except Exception as exc:
                self.after(0, lambda: self._set_status(f"Export hiba: {exc}", force=True))

        self._set_status("Word lista export folyamatban…", force=True)
        threading.Thread(target=work, daemon=True).start()

    def _export_list_pdf(self) -> None:
        """Aktuális (szűrt) lista → PDF-ek egy mappába."""
        messages = list(self._messages_cache)
        if not messages:
            messagebox.showinfo("Export", "Nincs exportálható levél a listában.")
            return
        folder = filedialog.askdirectory(title="PDF-ek mentési mappája")
        if not folder:
            return
        out_dir = Path(folder)

        def work() -> None:
            ok = 0
            err = 0
            try:
                for m in messages[:200]:
                    try:
                        full = get_message(m.id) or m
                        src = get_source(full.source_id)
                        if _is_stub_message(full.body_text or "", full.body_html or ""):
                            try:
                                refresh_one_message_html(full.id)
                                full = get_message(full.id) or full
                            except Exception:
                                pass
                        stem = self._export_filename_stem(
                            full.subject or "level",
                            when=full.received_at or "",
                            source_name=(src.name if src else "") or "hirlevel",
                        )
                        path = out_dir / f"{stem}.pdf"
                        # ütközés elkerülése
                        if path.exists():
                            path = out_dir / f"{stem}-{full.id}.pdf"
                        raw = (full.body_html or "").strip()
                        if not raw:
                            raw = self._plain_text_to_linked_html(
                                full.body_text or "(nincs tartalom)"
                            )
                        html_out = self._wrap_reader_html(raw)
                        export_message_to_pdf(path, full, source=src, html=html_out)
                        ok += 1
                    except Exception:
                        err += 1
                msg = f"PDF lista: {ok} kész"
                if err:
                    msg += f", {err} hiba"
                self.after(0, lambda: self._set_status(msg, force=True))
            except Exception as exc:
                self.after(0, lambda: self._set_status(f"PDF lista hiba: {exc}", force=True))

        self._set_status("PDF lista export folyamatban…", force=True)
        threading.Thread(target=work, daemon=True).start()

    def _set_status(self, text: str, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._status_ts < 0.35:
            return
        self._status_ts = now
        try:
            self.status.configure(text=text)
        except Exception:
            pass

    def _run_sync(self, *, full_import: bool) -> None:
        if self._syncing:
            return
        self._syncing = True
        self._set_status(
            "Teljes előzmény import… (lassú lehet)" if full_import else "Levelezés ellenőrzés…",
            force=True,
        )

        def work() -> None:
            summary = ""

            def progress(msg: str) -> None:
                self.after(0, lambda m=msg: self._set_status(m))

            try:
                totals = fetch_all_accounts(progress, full_import=full_import)
                total_new = sum(totals.values())
                if not totals:
                    summary = "Nincs beállított levelező fiók. Levelezés → Levelező fiókok…"
                else:
                    summary = f"Kész — {total_new} új levél. {datetime.now():%H:%M}"
            except Exception as exc:
                summary = f"Hiba: {exc}"

            def done() -> None:
                self._syncing = False
                self._reload_sources()
                q = self.search.get().strip()
                if q:
                    self._reload_messages(browse_source=False)
                elif self._selected:
                    self._reload_messages(browse_source=True)
                self._set_status(summary, force=True)

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _sync_async(self) -> None:
        self._run_sync(full_import=False)

    def _full_import_async(self) -> None:
        if not messagebox.askyesno(
            "Teljes import",
            "Ez végignézi az előzményeket is (lassabb).\nFolytatod?",
        ):
            return
        self._run_sync(full_import=True)

    def _schedule_poll(self) -> None:
        cfg = load_config()
        minutes = int(cfg.get("check_interval_minutes") or 15)
        minutes = max(5, minutes)
        ms = minutes * 60 * 1000

        def tick() -> None:
            if not self._syncing:
                self._sync_async()
            self._poll_job = self.after(ms, tick)

        self._poll_job = self.after(ms, tick)

    def _ensure_tray(self) -> None:
        if self._tray_icon is not None:
            return
        try:
            from app.tray import run_tray

            self._tray_icon = run_tray(
                on_show=lambda: self.after(0, self._show_from_tray),
                on_sync=lambda: self.after(0, self._sync_async),
                on_quit=lambda: self.after(0, self._quit_app),
            )
        except Exception as exc:
            self._tray_icon = None
            self._set_status(f"Tálca ikon hiba: {exc}", force=True)

    def _maximize(self) -> None:
        try:
            self.state("zoomed")
        except Exception:
            pass

    def _hide_to_tray(self) -> None:
        try:
            self._ensure_tray()
        except Exception:
            pass
        try:
            self.withdraw()
        except Exception:
            pass
        self._set_status("A program a tálcán fut (jobb klikk → Kilépés a teljes bezáráshoz).", force=True)

    def _show_from_tray(self) -> None:
        try:
            self.deiconify()
            self._maximize()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _on_close(self) -> None:
        """Ablak X / Alt+F4 → system tray, nem kilépés."""
        self._hide_to_tray()

    def _quit_app(self) -> None:
        if self._poll_job:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
        if self._backup_job:
            try:
                self.after_cancel(self._backup_job)
            except Exception:
                pass
        if self._tray_icon is not None:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
        self.destroy()
