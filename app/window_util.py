"""Ablak pozicionálási és méretezési segédeszközök."""

from __future__ import annotations

import customtkinter as ctk
from typing import Tuple


def center_window(window: ctk.CTkToplevel, width: int, height: int) -> None:
    """Ablak közepítése a szülőablakhoz képest."""
    window.geometry(f"{width}x{height}")
    
    # Szülőablak pozíciója és mérete (ha van)
    try:
        if hasattr(window, "master") and window.master:
            parent_x = window.master.winfo_x()
            parent_y = window.master.winfo_y()
            parent_width = window.master.winfo_width()
            parent_height = window.master.winfo_height()
        else:
            # Képernyő közepítés
            parent_x = 0
            parent_y = 0
            parent_width = window.winfo_screenwidth()
            parent_height = window.winfo_screenheight()
        
        # Új ablak pozíciója
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # Negatív koordináták elkerülése
        x = max(0, x)
        y = max(0, y)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        # Fallback: csak fix méret
        window.geometry(f"{width}x{height}")


def position_left_third(window: ctk.CTkToplevel, width: int, height: int) -> None:
    """Ablak pozicionálása a szülő ablak bal 1/3-ában."""
    window.geometry(f"{width}x{height}")
    
    try:
        if hasattr(window, "master") and window.master:
            parent_x = window.master.winfo_x()
            parent_y = window.master.winfo_y()
            parent_width = window.master.winfo_width()
            parent_height = window.master.winfo_height()
        else:
            parent_x = 0
            parent_y = 0
            parent_width = window.winfo_screenwidth()
            parent_height = window.winfo_screenheight()
        
        # Bal harmad közepítése
        x = parent_x + (parent_width // 3 - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        x = max(0, x)
        y = max(0, y)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        window.geometry(f"{width}x{height}")
