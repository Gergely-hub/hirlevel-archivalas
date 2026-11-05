"""Egyszeri / opcionális „Fontos tudnivalók” ablak induláskor."""

from __future__ import annotations

from typing import Callable, Optional

import tkinter as tk
import customtkinter as ctk

from app import help_text as ht
from app.db import load_config, save_config
from app.window_util import center_window

CONFIG_KEY = "important_notice_dismissed"


def should_show_at_startup(cfg: dict | None = None) -> bool:
    cfg = cfg or load_config()
    return not bool(cfg.get(CONFIG_KEY))


def show_important_notice(
    parent: ctk.CTk,
    *,
    on_open_legal: Optional[Callable[[], None]] = None,
    at_startup: bool = False,
) -> None:
    ImportantNoticeWindow(parent, on_open_legal=on_open_legal, at_startup=at_startup)


class ImportantNoticeWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent: ctk.CTk,
        *,
        on_open_legal: Optional[Callable[[], None]] = None,
        at_startup: bool = False,
    ) -> None:
        super().__init__(parent)
        self._on_open_legal = on_open_legal
        self._at_startup = at_startup

        self.title("Fontos tudnivalók")
        center_window(self, 620, 480)
        self.minsize(480, 360)
        self.transient(parent)
        self.grab_set()

        try:
            from pathlib import Path

            icon_path = Path(__file__).parent / "assets" / "hirlevel.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass

        header = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        header.pack(side="top", fill="x")
        ctk.CTkLabel(
            header,
            text="Fontos tudnivalók",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=12, padx=16, anchor="w")

        body = ctk.CTkTextbox(
            self,
            wrap="word",
            font=("Segoe UI", 13),
            activate_scrollbars=True,
        )
        body.pack(fill="both", expand=True, padx=16, pady=(8, 8))
        body.insert("1.0", ht.FONTOS_TUDNIVALOK.strip())
        body.configure(state="disabled")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=16, pady=(0, 14))

        self._hide_again_var = tk.BooleanVar(value=True)
        if at_startup:
            ctk.CTkCheckBox(
                footer,
                text="Ne jelenjen meg újra indításkor",
                variable=self._hide_again_var,
                font=("Segoe UI", 12),
            ).pack(anchor="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(fill="x")

        if on_open_legal is not None:
            ctk.CTkButton(
                btn_row,
                text="Jogi Dokumentumok Központ…",
                command=self._open_legal,
                width=220,
            ).pack(side="left")

        primary = "Tovább" if at_startup else "Bezárás"
        ctk.CTkButton(
            btn_row,
            text=primary,
            width=120,
            command=self._close,
        ).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(50, self.lift)
        self.focus_force()

    def _open_legal(self) -> None:
        if self._on_open_legal is not None:
            self._on_open_legal()

    def _close(self) -> None:
        if self._at_startup and self._hide_again_var.get():
            cfg = load_config()
            cfg[CONFIG_KEY] = True
            save_config(cfg)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
