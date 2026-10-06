"""Jogi Dokumentumok Központ - Tabbed dialógus ablak az alkalmazáson belül."""

from __future__ import annotations

import customtkinter as ctk
from tkinterweb import HtmlFrame
import os
from pathlib import Path

from app.window_util import center_window


class LegalCenterWindow(ctk.CTkToplevel):
    """Jogi dokumentumok megjelenítésére szolgáló ablak (tabbed interface)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Jogi Dokumentumok Központ")
        center_window(self, 1100, 750)
        self.minsize(800, 500)

        # Ablak közepítése
        self.transient(parent)
        self.grab_set()

        # Ikon (ha elérhető)
        try:
            icon_path = Path(__file__).parent / "assets" / "hirlevel.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass

        # Fejléc
        header_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        header_frame.pack(side="top", fill="x", padx=0, pady=0)

        header_label = ctk.CTkLabel(
            header_frame,
            text="Jogi Dokumentumok Központ",
            font=("Segoe UI", 16, "bold"),
            text_color=("gray10", "gray90"),
        )
        header_label.pack(pady=12, padx=16)

        # Tab-gombok frame
        tabs_frame = ctk.CTkFrame(self, fg_color=("gray80", "gray25"))
        tabs_frame.pack(side="top", fill="x", padx=0, pady=0)

        self.tab_buttons = {}
        self.tab_contents = {}
        self.current_tab = None

        tabs = [
            ("Adatkezelés", "ADATKEZELESI_TAJEKOZTATO.html", "data_protection"),
            ("Biztonság", "BIZTONSAG_ES_ADATVEDELEM.html", "security"),
            ("Felhasználási Feltételek", "FELHASZNALASI_FELTETELEK.html", "terms"),
            ("MIT-licenc", "LICENSE.html", "license"),
        ]

        for tab_label, html_file, tab_key in tabs:
            btn = ctk.CTkButton(
                tabs_frame,
                text=tab_label,
                width=150,
                height=35,
                fg_color=("gray70", "gray30"),
                hover_color=("gray60", "gray40"),
                text_color=("black", "white"),
                border_width=0,
                corner_radius=0,
                command=lambda k=tab_key, f=html_file: self._switch_tab(k, f),
            )
            btn.pack(side="left", padx=2, pady=2)
            self.tab_buttons[tab_key] = btn

        # Tartalom frame (HtmlFrame-et fog tartalmazni)
        self.content_frame = ctk.CTkFrame(self, fg_color=("white", "gray20"))
        self.content_frame.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        # Alsó gomb frame
        button_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        button_frame.pack(side="bottom", fill="x", padx=12, pady=12)

        close_button = ctk.CTkButton(
            button_frame,
            text="Bezárás",
            width=100,
            height=35,
            command=self.destroy,
        )
        close_button.pack(pady=6)

        # Első tab megnyitása
        self._switch_tab("data_protection", "ADATKEZELESI_TAJEKOZTATO.html")

    def _switch_tab(self, tab_key: str, html_file: str) -> None:
        """Tab-ra kattintás kezelése."""
        # Előző tartalom eltávolítása
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Tab gomb státusza frissítése (kijelölt tab másabb szín)
        for key, btn in self.tab_buttons.items():
            if key == tab_key:
                btn.configure(fg_color=("gray50", "gray50"))
            else:
                btn.configure(fg_color=("gray70", "gray30"))

        self.current_tab = tab_key

        # HTML fájl betöltése
        html_path = self._find_html_file(html_file)
        if html_path and os.path.exists(html_path):
            try:
                # HtmlFrame az alkalmazáson belül
                html_frame = HtmlFrame(self.content_frame)
                html_frame.pack(fill="both", expand=True, padx=0, pady=0)

                # HTML fájl betöltése
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                html_frame.load_html(html_content)

            except Exception as e:
                # Hiba esetén szöveg megjelenítése
                error_label = ctk.CTkLabel(
                    self.content_frame,
                    text=f"Nem sikerült betölteni a dokumentumot:\n{str(e)}",
                    text_color="red",
                )
                error_label.pack(fill="both", expand=True, padx=16, pady=16)
        else:
            # Fájl nem található
            error_label = ctk.CTkLabel(
                self.content_frame,
                text=f"Nem található: {html_file}",
                text_color="red",
            )
            error_label.pack(fill="both", expand=True, padx=16, pady=16)

    def _find_html_file(self, filename: str) -> str | None:
        """HTML fájl keresése a Hivatalos könyvtárban."""
        import sys
        
        # Lehetséges helyek (sorrendben)
        possible_paths = [
            # PyInstaller EXE mellett: Hivatalos/ mappa (program/Hivatalos/)
            os.path.join(os.path.dirname(sys.executable), "Hivatalos", filename),
            # Fejlesztői könyvtárban: Hivatalos/ mappa
            os.path.join(str(Path(__file__).parent.parent), "Hivatalos", filename),
            # Fallback: közvetlen a gyökérben (fejlesztés)
            os.path.join(str(Path(__file__).parent.parent), filename),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None


def show_legal_center(parent):
    """Jogi Dokumentumok Központ megnyitása."""
    LegalCenterWindow(parent)
