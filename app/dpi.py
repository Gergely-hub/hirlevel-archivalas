"""Windows DPI — CTk() előtt. Ne skálázzuk kétszer (OS + CTk), különben kilóg a jobb szél."""

from __future__ import annotations

import sys


def configure_windows_dpi() -> float:
    """Per-monitor DPI awareness. CTk() előtt hívd. Vissza: OS skála (információ)."""
    if sys.platform != "win32":
        return 1.0
    scale = 1.0
    try:
        import ctypes

        try:
            # PROCESS_PER_MONITOR_DPI_AWARE_V2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        user32 = ctypes.windll.user32
        hdc = user32.GetDC(0)
        dpi = int(ctypes.windll.gdi32.GetDeviceCaps(hdc, 88))
        user32.ReleaseDC(0, hdc)
        scale = max(1.0, round(dpi / 96.0, 2))
    except Exception:
        pass
    return scale


def apply_ctk_scaling(_scale: float) -> None:
    """CTk skálázás = 1.0. A Windows nagyítás (125%/150%) DPI-awareness-szel megy.

    Ha widget_scaling = OS-skála, a gombok nagyobbak, az ablak mérete nem —
    a jobb szél (Most ellenőriz, olvasó, ─□✕) levágódik. Ez volt a hiba.
    """
    import customtkinter as ctk

    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
