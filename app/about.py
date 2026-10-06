"""Program leírása — About ablak tabokkal és HTML megjelenítéssel."""

from __future__ import annotations

import customtkinter as ctk
from tkinterweb import HtmlFrame
import os
from pathlib import Path

from app.window_util import center_window


class AboutWindow(ctk.CTkToplevel):
    """Program leírása és információi."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("A Hírlevél Követőről")
        
        # Ablak közepítése
        center_window(self, 1100, 750)
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
            text="📧 Hírlevél Követő — A Programról",
            font=("Segoe UI", 18, "bold"),
            text_color=("gray10", "gray90"),
        )
        header_label.pack(pady=14, padx=16)

        # Tartalom: HTML frame
        content_frame = ctk.CTkFrame(self, fg_color=("white", "gray20"))
        content_frame.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        html_path = self._find_html_file("ROLUNK.html")
        if html_path and os.path.exists(html_path):
            try:
                html_frame = HtmlFrame(content_frame)
                html_frame.pack(fill="both", expand=True, padx=0, pady=0)

                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                html_frame.load_html(html_content)
            except Exception as e:
                error_label = ctk.CTkLabel(
                    content_frame,
                    text=f"Nem sikerült betölteni az információkat:\n{str(e)}",
                    text_color="red",
                )
                error_label.pack(fill="both", expand=True, padx=16, pady=16)
        else:
            error_label = ctk.CTkLabel(
                content_frame,
                text="Nem található: ROLUNK.html",
                text_color="red",
            )
            error_label.pack(fill="both", expand=True, padx=16, pady=16)

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

    def _find_html_file(self, filename: str) -> str | None:
        """HTML fájl keresése a Hivatalos könyvtárban vagy közvetlenül."""
        import sys
        
        # Lehetséges helyek (sorrendben)
        possible_paths = [
            # PyInstaller EXE mellett: Hivatalos/ mappa
            os.path.join(os.path.dirname(sys.executable), "Hivatalos", filename),
            # Fejlesztői könyvtárban: Hivatalos/ mappa
            os.path.join(str(Path(__file__).parent.parent), "Hivatalos", filename),
            # Fallback: közvetlenül a gyökérben (fejlesztés)
            os.path.join(str(Path(__file__).parent.parent), filename),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None


def show_about(parent):
    """A Programról ablak megnyitása."""
    AboutWindow(parent)
