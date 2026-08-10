from __future__ import annotations

import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw


def _default_icon() -> Image.Image:
    img = Image.new("RGB", (64, 64), color=(36, 99, 235))
    draw = ImageDraw.Draw(img)
    draw.rectangle((12, 18, 52, 46), outline=(255, 255, 255), width=3)
    draw.line((12, 18, 32, 34, 52, 18), fill=(255, 255, 255), width=3)
    return img


def run_tray(
    *,
    on_show: Callable[[], None],
    on_sync: Callable[[], None],
    on_quit: Callable[[], None],
) -> object:
    import pystray

    menu = pystray.Menu(
        pystray.MenuItem("Megnyitás", lambda: on_show(), default=True),
        pystray.MenuItem("Most ellenőriz", lambda: on_sync()),
        pystray.MenuItem("Kilépés", lambda: on_quit()),
    )
    icon = pystray.Icon("hirlevel_koveto", _default_icon(), "Hírlevél követő", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
