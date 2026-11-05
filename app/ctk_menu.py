from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

import customtkinter as ctk

# Nyitott legördülők (váltáskor mind bezárható)
_OPEN_POPUPS: list["CTkMenuPopup"] = []


@dataclass(frozen=True)
class MenuTheme:
    bar_bg: tuple[str, str]
    bar_text: tuple[str, str]
    popup_bg: tuple[str, str]
    hover: tuple[str, str]
    hover_text: tuple[str, str]
    text: tuple[str, str]
    muted: tuple[str, str]
    border: tuple[str, str]
    btn_hover: tuple[str, str]
    win_btn: tuple[str, str] = ("#E0E0E0", "#404040")
    win_btn_hover: tuple[str, str] = ("#C8C8C8", "#505050")
    win_btn_text: tuple[str, str] = ("#1A1A1A", "#F0F0F0")
    # Win11-szerű címsor: semleges hover, piros csak a ✕ felett
    win_caption_hover: tuple[str, str] = ("#E5E5E5", "#3F3F46")
    win_close_hover: tuple[str, str] = ("#E81123", "#C42B1C")
    win_close_text: tuple[str, str] = ("#FFFFFF", "#FFFFFF")


# Ablakvezérlők (Segoe MDL2) — vékony, natív kinézet
_WIN_GLYPH_MIN = "\uE921"
_WIN_GLYPH_MAX = "\uE922"
_WIN_GLYPH_RESTORE = "\uE923"
_WIN_GLYPH_CLOSE = "\uE8BB"


# CTk set_appearance_mode nélkül is a paletta appearance szerint választunk színt.
_UI_APPEARANCE: Optional[str] = None

_MENU_THEME = MenuTheme(
    bar_bg=("gray85", "gray20"),
    bar_text=("gray10", "gray90"),
    popup_bg=("gray90", "gray22"),
    hover=("gray70", "gray35"),
    hover_text=("gray10", "gray95"),
    text=("gray10", "gray90"),
    muted=("gray40", "gray65"),
    border=("gray70", "gray35"),
    btn_hover=("gray75", "gray30"),
)


def _attach_popup_hover(btn: ctk.CTkButton, th: MenuTheme) -> None:
    """Legördülő sor: hover = sötét sáv + kontrasztos szöveg.

    A CTk transparent gombokon a hover_color gyakran nem fest hátteret —
    ezért Enter/Leave alatt kézzel állítjuk a fg_color-t is.
    """

    def on_enter(_e: Any) -> None:
        try:
            btn.configure(
                fg_color=_pick_theme_color(th.hover),
                text_color=_pick_theme_color(th.hover_text),
                border_width=0,
            )
        except Exception:
            pass

    def on_leave(_e: Any) -> None:
        try:
            btn.configure(
                fg_color="transparent",
                text_color=_pick_theme_color(th.text),
                border_width=0,
            )
        except Exception:
            pass

    btn.bind("<Enter>", on_enter, add="+")
    btn.bind("<Leave>", on_leave, add="+")


def _caption_icon_font() -> ctk.CTkFont:
    try:
        return ctk.CTkFont(family="Segoe MDL2 Assets", size=11)
    except Exception:
        return ctk.CTkFont(size=13, weight="bold")


def set_ui_appearance(mode: str) -> None:
    global _UI_APPEARANCE
    _UI_APPEARANCE = mode if mode in ("Light", "Dark") else None


def _pick_theme_color(pair: tuple[str, str]) -> str:
    mode = _UI_APPEARANCE or ctk.get_appearance_mode()
    return pair[1] if mode == "Dark" else pair[0]


def _menu_btn_no_frame(btn: ctk.CTkButton, *, corner_radius: int = 0) -> None:
    """Főmenü / legördülő: ne örökölje a CTk téma gomb-keretét (border_width=1)."""
    try:
        btn.configure(border_width=0, corner_radius=corner_radius)
    except Exception:
        pass


def _attach_caption_hover(btn: ctk.CTkButton) -> None:
    """─ / □: átlátszó alap, hover-nél semleges szürke (CTk transparent + hover nem megbízható)."""
    if getattr(btn, "_caption_hover_bound", False):
        return
    btn._caption_hover_bound = True  # type: ignore[attr-defined]

    def on_enter(_e: Any) -> None:
        th = get_menu_theme()
        try:
            btn.configure(
                fg_color=_pick_theme_color(th.win_caption_hover),
                text_color=_pick_theme_color(th.win_btn_text),
            )
        except Exception:
            pass

    def on_leave(_e: Any) -> None:
        th = get_menu_theme()
        try:
            btn.configure(
                fg_color="transparent",
                text_color=_pick_theme_color(th.win_btn_text),
            )
        except Exception:
            pass

    btn.bind("<Enter>", on_enter, add="+")
    btn.bind("<Leave>", on_leave, add="+")


def _attach_close_caption_hover(btn: ctk.CTkButton) -> None:
    """✕: hover-nél piros háttér + fehér ikon."""
    if getattr(btn, "_caption_hover_bound", False):
        return
    btn._caption_hover_bound = True  # type: ignore[attr-defined]

    def on_enter(_e: Any) -> None:
        th = get_menu_theme()
        try:
            btn.configure(
                fg_color=_pick_theme_color(th.win_close_hover),
                text_color=_pick_theme_color(th.win_close_text),
            )
        except Exception:
            pass

    def on_leave(_e: Any) -> None:
        th = get_menu_theme()
        try:
            btn.configure(
                fg_color="transparent",
                text_color=_pick_theme_color(th.win_btn_text),
            )
        except Exception:
            pass

    btn.bind("<Enter>", on_enter, add="+")
    btn.bind("<Leave>", on_leave, add="+")


def _restyle_caption_buttons(btns: list[ctk.CTkButton], th: MenuTheme) -> None:
    if not btns:
        return
    txt = _pick_theme_color(th.win_btn_text)
    cap_hov = _pick_theme_color(th.win_caption_hover)
    close_hov = _pick_theme_color(th.win_close_hover)
    for i, btn in enumerate(btns):
        try:
            is_close = i == len(btns) - 1
            btn.configure(
                fg_color="transparent",
                text_color=txt,
                hover_color=close_hov if is_close else cap_hov,
            )
        except Exception:
            pass


def set_menu_theme(theme: MenuTheme) -> None:
    global _MENU_THEME
    _MENU_THEME = theme


def get_menu_theme() -> MenuTheme:
    return _MENU_THEME


def _force_destroy_popup(popup: "CTkMenuPopup") -> None:
    """Biztosan eltünteti a menüt (overrideredirect Toplevel is)."""
    try:
        popup._on_close = None  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        popup._cancel_leave()  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        child = getattr(popup, "_child", None)
        if child is not None:
            _force_destroy_popup(child)
            popup._child = None  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        popup._closed = True  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        popup.withdraw()
    except Exception:
        pass
    try:
        popup.destroy()
    except Exception:
        pass
    try:
        if popup in _OPEN_POPUPS:
            _OPEN_POPUPS.remove(popup)
    except Exception:
        pass


def close_all_menu_popups() -> None:
    for p in list(_OPEN_POPUPS):
        _force_destroy_popup(p)
    _OPEN_POPUPS.clear()


class CTkMenuPopup(ctk.CTkToplevel):
    """Témaszínes legördülő menü."""

    def __init__(
        self,
        master: Any,
        items: list[dict[str, Any]],
        *,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master)
        self.withdraw()
        self.overrideredirect(True)
        try:
            self.transient(master)
        except Exception:
            pass
        self._on_close = on_close
        self._child: Optional[CTkMenuPopup] = None
        self._closed = False
        self._leave_job: Optional[str] = None
        self._open_submenu_label: Optional[str] = None
        self._child_gen = 0
        _OPEN_POPUPS.append(self)

        th = _MENU_THEME
        self.configure(fg_color=th.popup_bg)
        wrap = ctk.CTkFrame(
            self,
            fg_color=th.popup_bg,
            corner_radius=6,
            border_width=1,
            border_color=th.border,
        )
        wrap.pack(fill="both", expand=True, padx=0, pady=0)

        for item in items:
            kind = item.get("kind", "command")
            if kind == "separator":
                ctk.CTkFrame(wrap, fg_color=th.border, height=1).pack(
                    fill="x", padx=8, pady=4
                )
                continue

            label = str(item.get("label") or "")
            if kind == "command":
                cmd = item.get("command")

                def run(c=cmd) -> None:
                    self._dismiss_all()
                    if c:
                        c()

                btn = ctk.CTkButton(
                    wrap,
                    text=label,
                    anchor="w",
                    height=32,
                    fg_color="transparent",
                    text_color=_pick_theme_color(th.text),
                    hover_color=_pick_theme_color(th.hover),
                    border_width=0,
                    corner_radius=0,
                    command=run,
                )
                _menu_btn_no_frame(btn)
                _attach_popup_hover(btn, th)
                btn.pack(fill="x", padx=4, pady=1)
                btn.bind("<Enter>", lambda _e: self._close_child(), add="+")

            elif kind == "check":
                var = item["variable"]
                cmd = item.get("command")

                def toggle(v=var, c=cmd) -> None:
                    v.set(not bool(v.get()))
                    self._dismiss_all()
                    if c:
                        c()

                mark = "✓  " if bool(var.get()) else "    "
                btn = ctk.CTkButton(
                    wrap,
                    text=f"{mark}{label}",
                    anchor="w",
                    height=32,
                    fg_color="transparent",
                    text_color=_pick_theme_color(th.text),
                    hover_color=_pick_theme_color(th.hover),
                    border_width=0,
                    corner_radius=0,
                    command=toggle,
                )
                _menu_btn_no_frame(btn)
                _attach_popup_hover(btn, th)
                btn.pack(fill="x", padx=4, pady=1)
                btn.bind("<Enter>", lambda _e: self._close_child(), add="+")

            elif kind == "radio":
                var = item["variable"]
                value = item["value"]
                cmd = item.get("command")
                try:
                    selected = var.get() == value
                except Exception:
                    selected = str(var.get()) == str(value)
                mark = "●  " if selected else "○  "

                def choose(v=var, val=value, c=cmd) -> None:
                    v.set(val)
                    if c:
                        c()
                    self._dismiss_all()

                btn = ctk.CTkButton(
                    wrap,
                    text=f"{mark}{label}",
                    anchor="w",
                    height=32,
                    fg_color="transparent",
                    text_color=_pick_theme_color(th.text),
                    hover_color=_pick_theme_color(th.hover),
                    border_width=0,
                    corner_radius=0,
                    command=choose,
                )
                _menu_btn_no_frame(btn)
                _attach_popup_hover(btn, th)
                btn.pack(fill="x", padx=4, pady=1)
                btn.bind("<Enter>", lambda _e: self._close_child(), add="+")

            elif kind == "submenu":
                self._add_submenu_flyout(wrap, label, item.get("items") or [])

        self.bind("<Escape>", lambda _e: self._dismiss_all())
        self.bind("<Enter>", lambda _e: self._cancel_leave(), add="+")

    def _cancel_leave(self) -> None:
        if self._leave_job is not None:
            try:
                self.after_cancel(self._leave_job)
            except Exception:
                pass
            self._leave_job = None

    def _close_child(self) -> None:
        self._cancel_leave()
        self._open_submenu_label = None
        self._child_gen += 1
        if self._child is not None:
            child = self._child
            self._child = None
            _force_destroy_popup(child)

    def _schedule_close_child(self, gen: Optional[int] = None) -> None:
        self._cancel_leave()
        expect = self._child_gen if gen is None else gen

        def maybe_close() -> None:
            self._leave_job = None
            if expect != self._child_gen:
                return
            try:
                x = self.winfo_pointerx()
                y = self.winfo_pointery()
            except Exception:
                self._close_child()
                return
            if self.contains_point(x, y):
                return
            self._close_child()

        self._leave_job = self.after(120, maybe_close)

    def _add_submenu_flyout(
        self, wrap: Any, label: str, sub_items: list[dict[str, Any]]
    ) -> None:
        """Egér a soron → almenü jobbra nyílik (Windows-szerű)."""
        hover_job: dict[str, Any] = {"id": None}
        th = _MENU_THEME

        def cancel_hover() -> None:
            job = hover_job.get("id")
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                hover_job["id"] = None

        def open_flyout(_event: Any = None) -> None:
            self._cancel_leave()
            cancel_hover()
            if (
                self._child is not None
                and self._open_submenu_label == label
                and not getattr(self._child, "_closed", False)
            ):
                try:
                    self._child.lift()
                    return
                except Exception:
                    pass
            self._close_child()
            self.update_idletasks()
            x = self.winfo_rootx() + max(self.winfo_width(), 1) - 2
            y = header.winfo_rooty()
            child = CTkMenuPopup(self, sub_items)
            child._submenu_label = label  # type: ignore[attr-defined]
            child.update_idletasks()
            req_w = max(child.winfo_reqwidth(), 140)
            screen_w = self.winfo_screenwidth()
            if x + req_w > screen_w - 4:
                x = self.winfo_rootx() - req_w + 4
            self._child = child
            self._open_submenu_label = label
            self._child_gen += 1
            child.show_at(x, y)
            child.bind("<Enter>", lambda _e: self._cancel_leave(), add="+")
            gen = self._child_gen
            child.bind(
                "<Leave>",
                lambda _e, g=gen: self._schedule_close_child(g),
                add="+",
            )

        def on_enter(_event: Any = None) -> None:
            self._cancel_leave()
            cancel_hover()
            delay = 0 if self._child is not None else 30
            hover_job["id"] = self.after(delay, open_flyout)

        def on_leave(_event: Any = None) -> None:
            cancel_hover()
            self._schedule_close_child(self._child_gen)

        header = ctk.CTkButton(
            wrap,
            text=f"{label}  ›",
            anchor="w",
            height=32,
            fg_color="transparent",
            text_color=_pick_theme_color(th.text),
            hover_color=_pick_theme_color(th.hover),
            border_width=0,
            corner_radius=0,
            command=open_flyout,
        )
        _menu_btn_no_frame(header)
        _attach_popup_hover(header, th)
        header.pack(fill="x", padx=4, pady=1)
        header.bind("<Enter>", on_enter, add="+")
        header.bind("<Leave>", on_leave, add="+")

    def contains_point(self, x: int, y: int) -> bool:
        try:
            left, top = self.winfo_rootx(), self.winfo_rooty()
            right = left + max(self.winfo_width(), 1)
            bottom = top + max(self.winfo_height(), 1)
            if left <= x < right and top <= y < bottom:
                return True
            if self._child is not None and self._child.contains_point(x, y):
                return True
        except Exception:
            return False
        return False

    def show_at(self, x: int, y: int) -> None:
        self.update_idletasks()
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.lift()

    def destroy_silent(self) -> None:
        """Bezárás anélkül, hogy az on_close leállítaná a menüsáv módot."""
        self._on_close = None
        _force_destroy_popup(self)

    def _dismiss_all(self) -> None:
        if self._closed:
            return
        cb = self._on_close
        self._on_close = None
        master = self.master
        top: CTkMenuPopup = self
        while master is not None:
            if isinstance(master, CTkMenuPopup):
                top = master
                try:
                    master = master.master
                except Exception:
                    break
            else:
                break
        if top is not self:
            top._dismiss_all()
            return
        _force_destroy_popup(self)
        if cb:
            cb()


class CTkMenuBar(ctk.CTkFrame):
    """Menüsor: bal = menük, közép = húzás, jobb = ─ □ ✕ (Win11-szerű)."""

    _BAR_H = 46
    _BTN_W = 48
    _BTN_H = 34
    _CONTROLS_W = 144

    def __init__(
        self,
        master: Any,
        menus: list[tuple[str, list[dict[str, Any]]]],
        *,
        on_minimize: Optional[Callable[[], None]] = None,
        on_toggle_max: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        th = _MENU_THEME
        super().__init__(master, corner_radius=0, height=self._BAR_H, fg_color=th.bar_bg)
        self.pack_propagate(False)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=self._CONTROLS_W)
        self._popup: Optional[CTkMenuPopup] = None
        self._menus = menus
        self._outside_bound = False
        self._focus_bound = False
        self._menu_buttons: list[ctk.CTkButton] = []
        self._active_button: Optional[ctk.CTkButton] = None
        self._menu_active = False
        self._win_btns: list[ctk.CTkButton] = []
        self._max_btn: Optional[ctk.CTkButton] = None
        self._glyph_max = _WIN_GLYPH_MAX
        self._glyph_restore = _WIN_GLYPH_RESTORE
        self._drag_area: Optional[ctk.CTkFrame] = None
        self._drag_xy: Optional[tuple[int, int]] = None
        self._on_toggle_max = on_toggle_max

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(4, 0), pady=4)

        for title, items in menus:
            # Szöveghez igazított szélesség — ne vágja le a „Beállítások”-t
            btn_w = max(56, 11 * len(title) + 28)
            btn = ctk.CTkButton(
                left,
                text=title,
                width=btn_w,
                height=32,
                corner_radius=0,
                border_width=0,
                fg_color="transparent",
                text_color=_pick_theme_color(th.bar_text),
                hover_color=_pick_theme_color(th.btn_hover),
            )
            _menu_btn_no_frame(btn)
            btn.pack(side="left", padx=2)
            btn.configure(command=lambda button=btn, it=items: self._on_click(button, it))
            btn.bind(
                "<Enter>",
                lambda _e, button=btn, it=items: self._on_menubar_enter(button, it),
                add="+",
            )
            self._menu_buttons.append(btn)

        drag = ctk.CTkFrame(self, fg_color="transparent", height=28)
        drag.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._drag_area = drag

        def start_drag(event: Any) -> None:
            self._drag_xy = (int(event.x_root), int(event.y_root))

        def do_drag(event: Any) -> None:
            if self._drag_xy is None:
                return
            root = self.winfo_toplevel()
            try:
                from app.win_chrome import is_maximized

                if is_maximized(root) or getattr(root, "_win_maximized", False):
                    return
            except Exception:
                pass
            dx = int(event.x_root) - self._drag_xy[0]
            dy = int(event.y_root) - self._drag_xy[1]
            self._drag_xy = (int(event.x_root), int(event.y_root))
            try:
                root.geometry(f"+{root.winfo_x() + dx}+{root.winfo_y() + dy}")
            except Exception:
                pass

        def end_drag(_event: Any = None) -> None:
            self._drag_xy = None

        def dbl_max(_event: Any = None) -> None:
            if self._on_toggle_max:
                self._on_toggle_max()

        for w in (drag,):
            w.bind("<ButtonPress-1>", start_drag)
            w.bind("<B1-Motion>", do_drag)
            w.bind("<ButtonRelease-1>", end_drag)
            w.bind("<Double-Button-1>", dbl_max)

        if on_minimize and on_toggle_max and on_close:
            controls = ctk.CTkFrame(self, fg_color="transparent", width=self._CONTROLS_W)
            controls.grid(row=0, column=2, sticky="e", padx=(0, 0), pady=5)
            controls.grid_propagate(False)
            win_font = _caption_icon_font()
            th = get_menu_theme()
            icon_col = _pick_theme_color(th.win_btn_text)

            def mk(text: str, cmd: Callable[[], None], *, close: bool = False) -> ctk.CTkButton:
                hov = _pick_theme_color(
                    th.win_close_hover if close else th.win_caption_hover
                )
                b = ctk.CTkButton(
                    controls,
                    text=text,
                    width=self._BTN_W,
                    height=self._BTN_H,
                    corner_radius=0,
                    border_width=0,
                    font=win_font,
                    fg_color="transparent",
                    text_color=icon_col,
                    hover_color=hov,
                    command=cmd,
                )
                _menu_btn_no_frame(b)
                b.pack(side="left")
                if close:
                    _attach_close_caption_hover(b)
                else:
                    _attach_caption_hover(b)
                self._win_btns.append(b)
                return b

            mk(_WIN_GLYPH_MIN, on_minimize)
            self._max_btn = mk(_WIN_GLYPH_RESTORE, on_toggle_max)  # indulás: work area
            mk(_WIN_GLYPH_CLOSE, on_close, close=True)

        self._bind_focus_loss()

    def apply_theme(self, theme: MenuTheme) -> None:
        set_menu_theme(theme)
        try:
            self.configure(fg_color=theme.bar_bg)
        except Exception:
            pass
        for btn in self._menu_buttons:
            try:
                btn.configure(
                    text_color=_pick_theme_color(theme.bar_text),
                    hover_color=_pick_theme_color(theme.btn_hover),
                    border_width=0,
                    corner_radius=0,
                )
            except Exception:
                pass
        _restyle_caption_buttons(self._win_btns, theme)

    def set_maximize_icon(self, maximized: bool) -> None:
        """Maximalizálva: restore (két négyzet). Ablakos: maximize (egy négyzet)."""
        btn = getattr(self, "_max_btn", None)
        if btn is None:
            return
        glyph = self._glyph_restore if maximized else self._glyph_max
        try:
            btn.configure(text=glyph)
        except Exception:
            pass

    def enable_window_chrome(
        self,
        *,
        on_minimize: Callable[[], None],
        on_toggle_max: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        """Régi API — a gombok már az __init__-ben készülnek."""
        pass

    def _pointer_over_menu_ui(self, x: int, y: int) -> bool:
        if self._popup is not None and self._popup.contains_point(x, y):
            return True
        for p in list(_OPEN_POPUPS):
            try:
                if p.contains_point(x, y):
                    return True
            except Exception:
                continue
        for btn in self._menu_buttons:
            try:
                bx, by = btn.winfo_rootx(), btn.winfo_rooty()
                if bx <= x < bx + btn.winfo_width() and by <= y < by + btn.winfo_height():
                    return True
            except Exception:
                continue
        try:
            mx, my = self.winfo_rootx(), self.winfo_rooty()
            if mx <= x < mx + self.winfo_width() and my <= y < my + self.winfo_height():
                return True
        except Exception:
            pass
        return False

    def _close_popup(self, *, silent: bool = False) -> None:
        popup = self._popup
        self._popup = None
        self._active_button = None
        keep_cb = None
        if popup is not None and not silent:
            keep_cb = getattr(popup, "_on_close", None)
            try:
                popup._on_close = None
            except Exception:
                pass
        close_all_menu_popups()
        if keep_cb:
            try:
                keep_cb()
            except Exception:
                pass
        try:
            root = self.winfo_toplevel()
            for child in list(root.winfo_children()):
                if isinstance(child, CTkMenuPopup):
                    _force_destroy_popup(child)
        except Exception:
            pass

    def _end_menu_mode(self) -> None:
        self._menu_active = False
        self._close_popup(silent=True)

    def _bind_outside(self) -> None:
        if self._outside_bound:
            return
        root = self.winfo_toplevel()

        def on_press(event: Any) -> None:
            if self._popup is None and not _OPEN_POPUPS:
                return
            try:
                x, y = int(event.x_root), int(event.y_root)
            except Exception:
                self.after(1, self._end_menu_mode)
                return
            if self._pointer_over_menu_ui(x, y):
                return
            self.after(1, self._end_menu_mode)

        root.bind_all("<ButtonPress-1>", on_press, add="+")
        self._outside_bound = True

    def _bind_focus_loss(self) -> None:
        if self._focus_bound:
            return
        root = self.winfo_toplevel()

        def close_soon(_event: Any = None) -> None:
            if self._popup is None and not _OPEN_POPUPS:
                return

            def check() -> None:
                if not self._menu_active:
                    return
                try:
                    x, y = self.winfo_pointerx(), self.winfo_pointery()
                except Exception:
                    return
                if self._pointer_over_menu_ui(x, y):
                    return
                self._end_menu_mode()

            self.after(80, check)

        root.bind("<Deactivate>", close_soon, add="+")
        self._focus_bound = True

    def _on_click(self, button: ctk.CTkButton, items: list[dict[str, Any]]) -> None:
        if self._menu_active and self._active_button is button:
            self._end_menu_mode()
            return
        self._menu_active = True
        self._open_menu(button, items)

    def _on_menubar_enter(self, button: ctk.CTkButton, items: list[dict[str, Any]]) -> None:
        if not self._menu_active:
            return
        if self._active_button is button and self._popup is not None:
            return
        self._open_menu(button, items)

    def _open_menu(self, button: ctk.CTkButton, items: list[dict[str, Any]]) -> None:
        self._close_popup(silent=True)
        self._menu_active = True
        self.update_idletasks()
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height() + 2
        self._active_button = button

        def on_close() -> None:
            if self._popup is not None:
                self._popup = None
            self._menu_active = False
            self._active_button = None

        self._popup = CTkMenuPopup(self.winfo_toplevel(), items, on_close=on_close)
        self._popup.show_at(x, y)
        self._bind_outside()
