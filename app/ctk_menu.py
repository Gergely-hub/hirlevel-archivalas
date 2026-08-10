from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

# Nyitott legördülők (váltáskor mind bezárható)
_OPEN_POPUPS: list["CTkMenuPopup"] = []


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
    """Sötét/világos témát követő legördülő menü."""

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
        self._child_gen = 0  # elavult close-job ellen
        _OPEN_POPUPS.append(self)

        self.configure(fg_color=("gray90", "gray17"))
        wrap = ctk.CTkFrame(
            self,
            fg_color=("gray90", "gray17"),
            corner_radius=6,
            border_width=1,
            border_color=("gray70", "gray35"),
        )
        wrap.pack(fill="both", expand=True, padx=0, pady=0)

        for item in items:
            kind = item.get("kind", "command")
            if kind == "separator":
                ctk.CTkFrame(wrap, fg_color=("gray70", "gray40"), height=1).pack(
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
                    text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray30"),
                    command=run,
                )
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
                    text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray30"),
                    command=toggle,
                )
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
                    text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray30"),
                    command=choose,
                )
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
            # Másik almenü már nyitva → azonnal vált
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
            text_color=("gray10", "gray90"),
            hover_color=("gray80", "gray30"),
            command=open_flyout,
        )
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
        # Először a lánc teteje (menüsáv popup), hogy egy hívás mindent zárjon
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
    """CustomTkinter menüsáv — kattintás nyit, utána egérrel vált."""

    def __init__(self, master: Any, menus: list[tuple[str, list[dict[str, Any]]]]) -> None:
        super().__init__(master, corner_radius=0, height=36, fg_color=("gray85", "gray20"))
        self.pack_propagate(False)
        self._popup: Optional[CTkMenuPopup] = None
        self._menus = menus
        self._outside_bound = False
        self._focus_bound = False
        self._menu_buttons: list[ctk.CTkButton] = []
        self._active_button: Optional[ctk.CTkButton] = None
        self._menu_active = False  # True: egérrel is válthat a menük között

        for title, items in menus:
            btn = ctk.CTkButton(
                self,
                text=title,
                width=84,
                height=28,
                corner_radius=4,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray30"),
            )
            btn.pack(side="left", padx=2, pady=4)
            btn.configure(command=lambda button=btn, it=items: self._on_click(button, it))
            btn.bind(
                "<Enter>",
                lambda _e, button=btn, it=items: self._on_menubar_enter(button, it),
                add="+",
            )
            self._menu_buttons.append(btn)

        self._bind_focus_loss()

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
        # Extra: root alatt maradt CTkMenuPopup
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
                # Popup / menüsáv fölött: a Toplevel miatt jött Deactivate — ne zárjuk
                if self._pointer_over_menu_ui(x, y):
                    return
                self._end_menu_mode()

            self.after(80, check)

        root.bind("<Deactivate>", close_soon, add="+")
        self._focus_bound = True

    def _on_click(self, button: ctk.CTkButton, items: list[dict[str, Any]]) -> None:
        # Ugyanarra kattintás → zár
        if self._menu_active and self._active_button is button:
            self._end_menu_mode()
            return
        self._menu_active = True
        self._open_menu(button, items)

    def _on_menubar_enter(self, button: ctk.CTkButton, items: list[dict[str, Any]]) -> None:
        # Csak ha már kattintással megnyílt egy menü — egérrel vált
        if not self._menu_active:
            return
        if self._active_button is button and self._popup is not None:
            return
        self._open_menu(button, items)

    def _open_menu(self, button: ctk.CTkButton, items: list[dict[str, Any]]) -> None:
        # Előző menü(k) biztos bezárása váltáskor
        self._close_popup(silent=True)
        self._menu_active = True
        self.update_idletasks()
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height() + 2
        self._active_button = button

        def on_close() -> None:
            # Parancs választása / Escape — menümód vége
            if self._popup is not None:
                self._popup = None
            self._menu_active = False
            self._active_button = None

        self._popup = CTkMenuPopup(self.winfo_toplevel(), items, on_close=on_close)
        self._popup.show_at(x, y)
        self._bind_outside()
