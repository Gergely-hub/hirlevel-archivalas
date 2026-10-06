from __future__ import annotations

"""Kék boríték ikon — tálca, system tray és .exe közös forrása."""

from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw

# Tray / UI kék
_BLUE = (36, 99, 235)
_WHITE = (255, 255, 255)


def make_envelope_image(size: int = 256) -> Image.Image:
    """Kék négyzet, fehér boríték — ugyanaz, mint a system tray."""
    s = max(16, int(size))
    img = Image.new("RGBA", (s, s), (*_BLUE, 255))
    draw = ImageDraw.Draw(img)
    # Arányok a 64×64 tray ikonhoz igazítva
    m = s / 64.0
    left, top, right, bottom = 12 * m, 18 * m, 52 * m, 46 * m
    mid_x, fold_y = 32 * m, 34 * m
    w = max(2, int(round(3 * m)))
    draw.rectangle((left, top, right, bottom), outline=_WHITE, width=w)
    draw.line((left, top, mid_x, fold_y, right, top), fill=_WHITE, width=w)
    return img


def icon_candidates() -> list[Path]:
    here = Path(__file__).resolve().parent
    project = here.parent
    out: list[Path] = []
    try:
        import sys

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            out.append(Path(sys._MEIPASS) / "app" / "assets" / "hirlevel.ico")
            out.append(Path(sys._MEIPASS) / "hirlevel.ico")
        if getattr(sys, "frozen", False):
            out.append(Path(sys.executable).resolve().parent / "hirlevel.ico")
    except Exception:
        pass
    out.append(here / "assets" / "hirlevel.ico")
    out.append(project / "app" / "assets" / "hirlevel.ico")
    out.append(project / "hirlevel.ico")
    return out


def resolve_ico_path() -> Optional[Path]:
    for p in icon_candidates():
        if p.is_file():
            return p
    return None


def write_ico(path: Path) -> Path:
    """Többméretű .ico Windows tálcához / PyInstallerhez."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = [make_envelope_image(sz).convert("RGBA") for sz in sizes]
    # Pillow: legnagyobb + append_images a többi mérethez
    images[-1].save(
        path,
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[:-1],
    )
    return path


def ensure_ico() -> Path:
    existing = resolve_ico_path()
    if existing is not None:
        return existing
    dest = Path(__file__).resolve().parent / "assets" / "hirlevel.ico"
    return write_ico(dest)


def apply_window_icon(widget: Any) -> None:
    """Tk/CTk ablak + Windows taskbar ikon (frameless után is)."""
    try:
        ico = ensure_ico()
    except Exception:
        ico = None

    try:
        from PIL import ImageTk

        photos = []
        for sz in (16, 32, 48, 256):
            photos.append(ImageTk.PhotoImage(make_envelope_image(sz)))
        widget.iconphoto(True, *photos)
        widget._app_icon_photos = photos  # type: ignore[attr-defined]
    except Exception:
        pass

    if ico is not None:
        try:
            widget.iconbitmap(default=str(ico))
        except Exception:
            try:
                widget.iconbitmap(str(ico))
            except Exception:
                pass
        _win32_set_icons(widget, ico)


def _win32_set_icons(widget: Any, ico: Path) -> None:
    try:
        import ctypes
        from ctypes import wintypes

        from app.win_chrome import hwnd_of

        widget.update_idletasks()
        hwnd = hwnd_of(widget)
        if not hwnd:
            return

        user32 = ctypes.windll.user32
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        LoadImageW = user32.LoadImageW
        LoadImageW.argtypes = [
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        LoadImageW.restype = wintypes.HANDLE

        path = str(ico)
        h_small = LoadImageW(None, path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        h_big = LoadImageW(None, path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        if not h_big:
            h_big = LoadImageW(None, path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if h_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_small)
        if h_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_big)
    except Exception:
        pass
