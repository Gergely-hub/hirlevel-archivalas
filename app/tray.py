from __future__ import annotations

import threading
from typing import Callable

from app.app_icon import make_envelope_image


def run_tray(
    *,
    on_toggle: Callable[[], None],
    on_sync: Callable[[], None],
    on_quit: Callable[[], None],
) -> object:
    import pystray

    menu = pystray.Menu(
        pystray.MenuItem("Megnyitás / elrejtés", lambda: on_toggle(), default=True),
        pystray.MenuItem("Most ellenőriz", lambda: on_sync()),
        pystray.MenuItem("Kilépés", lambda: on_quit()),
    )
    icon = pystray.Icon(
        "hirlevel_koveto",
        make_envelope_image(64).convert("RGB"),
        "Hírlevél követő",
        menu,
    )
    threading.Thread(target=icon.run, daemon=True).start()
    return icon

