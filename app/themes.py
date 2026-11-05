from __future__ import annotations

"""UI színsémák — klasszikus Világos/Sötét (levelező) + hangulat témák."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


THEMES_DIR = Path(__file__).resolve().parent / "theme_assets"


def _themes_dir() -> Path:
    bundled = Path(__file__).resolve().parent / "theme_assets"
    if bundled.is_dir():
        return bundled
    try:
        from app.paths import ROOT

        d = ROOT / "theme_assets"
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        return bundled


@dataclass(frozen=True)
class ThemePalette:
    id: str
    label: str
    appearance: str  # Light | Dark
    ctk_theme: str
    window_bg: tuple[str, str]
    left_bg: tuple[str, str]
    mid_bg: tuple[str, str]
    menubar_bg: tuple[str, str]
    menubar_fg: tuple[str, str]
    accent: tuple[str, str]
    accent_hover: tuple[str, str]
    source_row: tuple[str, str]
    source_active: tuple[str, str]
    source_hover: tuple[str, str]
    bubble: tuple[str, str]
    bubble_unread: tuple[str, str]
    bubble_sel: tuple[str, str]
    day_bar: tuple[str, str]
    muted: tuple[str, str]
    text: tuple[str, str]
    uj_bg: tuple[str, str]
    uj_fg: tuple[str, str]
    reader_bg: str
    reader_fg: str
    primary: tuple[str, str]
    primary_hover: tuple[str, str]
    btn_text: tuple[str, str]
    surface: tuple[str, str]


# Klasszikus világos levelező (semleges szürke + kék)
_LIGHT_CLASSIC: dict[str, str] = {
    "background": "#fafafa",
    "backgroundAlt": "#f1f3f4",
    "surface": "#ffffff",
    "text": "#202124",
    "textMuted": "#5f6368",
    "textOnDark": "#ffffff",
    "primary": "#1a73e8",
    "primaryMid": "#1557b0",
    "accent": "#1a73e8",
    "accentLight": "#f1f3f4",
    "accentDark": "#1557b0",
    "chip": "#e8f0fe",
    "chipActive": "#d2e3fc",
}

_MOBILE_THEMES: list[dict[str, Any]] = [
    {
        # Felkelő nap, megvilágított táj
        "id": "frissReggel",
        "label": "Friss reggel",
        "dark_ui": False,
        "c": {
            "background": "#faf3e8",
            "backgroundAlt": "#f3e4cf",
            "surface": "#fffefb",
            "text": "#2c241c",
            "textMuted": "#6b6358",
            "textOnDark": "#ffffff",
            "primary": "#c4783a",
            "primaryMid": "#a8622e",
            "accent": "#e8b86d",
            "accentLight": "#e4ecd8",
            "accentDark": "#c4863a",
            "chip": "#f5e8d4",
            "chipActive": "#c4783a",
            "leftPanel": "#f3e4cf",
            "bubbleSel": "#f5e8d4",
            "sourceHover": "#ede4d4",
        },
    },
    {
        # Mély éjkék + csillogó égszín (gombkeret: accentDark)
        "id": "ejfelt",
        "label": "Éjfél",
        "dark_ui": True,
        "c": {
            "background": "#070b14",
            "backgroundAlt": "#0f172a",
            "surface": "#1e293b",
            "text": "#e8eef9",
            "textMuted": "#94a3b8",
            "textOnDark": "#ffffff",
            "primary": "#2563eb",
            "primaryMid": "#1d4ed8",
            "accent": "#38bdf8",
            "accentLight": "#1e3a5f",
            "accentDark": "#7dd3fc",
            "chip": "#1e293b",
            "chipActive": "#1d4ed8",
        },
    },
    {
        "id": "kave",
        "label": "Kávé",
        "dark_ui": False,
        "c": {
            "background": "#f2ebe4",
            "backgroundAlt": "#e8dfd6",
            "surface": "#faf6f2",
            "text": "#2a2018",
            "textMuted": "#7a6e64",
            "textOnDark": "#faf6f0",
            "primary": "#4a3228",
            "primaryMid": "#6b4a3a",
            "accent": "#a67c52",
            "accentLight": "#d4b898",
            "accentDark": "#846040",
            "chip": "#ebe0d4",
            "chipActive": "#4a3228",
        },
    },
    {
        # Part: világos hab; mélység: primary / menü mélykék; accent: napfény a vízen
        "id": "ocean",
        "label": "Óceán",
        "dark_ui": False,
        "c": {
            "background": "#eff9fc",
            "backgroundAlt": "#d9f0f7",
            "surface": "#ffffff",
            "text": "#0b2e3a",
            "textMuted": "#4a6d78",
            "textOnDark": "#ecfeff",
            "primary": "#0c4a6e",
            "primaryMid": "#075985",
            "accent": "#22d3ee",
            "accentLight": "#b8e4f2",
            "accentDark": "#0284c7",
            "chip": "#cffafe",
            "chipActive": "#0c4a6e",
        },
    },
    {
        # Sötétebb barna papír, mint a Világos alap
        "id": "tompaPapir",
        "label": "Tompa papír",
        "dark_ui": False,
        "c": {
            "background": "#e8e2d6",
            "backgroundAlt": "#d4cdc0",
            "surface": "#f5f2ec",
            "text": "#1c2420",
            "textMuted": "#5f6b64",
            "textOnDark": "#f4f7f5",
            "primary": "#5c4f42",
            "primaryMid": "#4a4036",
            "accent": "#7a9278",
            "accentLight": "#b8bfb0",
            "accentDark": "#5f7560",
            "chip": "#ccc4b6",
            "chipActive": "#5c4f42",
        },
    },
]


def _pair(light: str, dark: str) -> tuple[str, str]:
    return (light, dark)


def _ctk_from_mobile(c: dict[str, str], *, dark_ui: bool) -> dict[str, Any]:
    """CTk JSON a mobil színekből."""
    bg = c["background"]
    bg_alt = c["backgroundAlt"]
    surface = c["surface"]
    text = c["text"]
    muted = c["textMuted"]
    primary = c["primary"]
    mid = c["primaryMid"]
    accent = c["accent"]
    accent_dark = c["accentDark"]
    accent_light = c["accentLight"]
    on_dark = c["textOnDark"]
    # CTk: index 0 = Light mód, 1 = Dark mód — mindkét slotot kitöltjük ugyanazzal a palettával
    a0, a1 = (bg, bg) if not dark_ui else (bg, bg)
    s0, s1 = (surface, surface)
    t0, t1 = (text, text)
    p0, p1 = (primary, primary)
    ac0, ac1 = (accent, accent)
    ad0, ad1 = (accent_dark, accent_dark)
    btn_text = on_dark if _is_dark_hex(primary) else text
    return {
        "CTk": {"fg_color": [a0, a1]},
        "CTkToplevel": {"fg_color": [a0, a1]},
        "CTkFrame": {
            "corner_radius": 6,
            "border_width": 0,
            "fg_color": [bg_alt, bg_alt],
            "top_fg_color": [s0, s1],
            "border_color": [muted, muted],
        },
        "CTkButton": {
            "corner_radius": 7,
            "border_width": 1,
            "fg_color": [p0, p1],
            "hover_color": [mid, mid],
            "border_color": [ad0, ad1],
            "text_color": [btn_text, btn_text],
            "text_color_disabled": [muted, muted],
        },
        "CTkLabel": {
            "corner_radius": 0,
            "border_width": 0,
            "fg_color": "transparent",
            "border_color": [muted, muted],
            "text_color": [t0, t1],
        },
        "CTkEntry": {
            "corner_radius": 6,
            "border_width": 2,
            "fg_color": [s0, s1],
            "border_color": [muted, muted],
            "text_color": [t0, t1],
            "placeholder_text_color": [muted, muted],
        },
        "CTkCheckBox": {
            "corner_radius": 6,
            "border_width": 3,
            "fg_color": [ac0, ac1],
            "border_color": [muted, muted],
            "hover_color": [ad0, ad1],
            "checkmark_color": [btn_text, btn_text],
            "text_color": [t0, t1],
            "text_color_disabled": [muted, muted],
        },
        "CTkSwitch": {
            "corner_radius": 1000,
            "border_width": 3,
            "button_length": 0,
            "fg_color": [muted, muted],
            "progress_color": [ac0, ac1],
            "button_color": [s0, s1],
            "button_hover_color": [accent_light, accent_light],
            "text_color": [t0, t1],
            "text_color_disabled": [muted, muted],
        },
        "CTkRadioButton": {
            "corner_radius": 1000,
            "border_width_checked": 4,
            "border_width_unchecked": 2,
            "fg_color": [ac0, ac1],
            "border_color": [muted, muted],
            "hover_color": [ad0, ad1],
            "text_color": [t0, t1],
            "text_color_disabled": [muted, muted],
        },
        "CTkProgressBar": {
            "corner_radius": 1000,
            "border_width": 0,
            "fg_color": [muted, muted],
            "progress_color": [ac0, ac1],
            "border_color": ["gray", "gray"],
        },
        "CTkSlider": {
            "corner_radius": 1000,
            "button_corner_radius": 1000,
            "border_width": 6,
            "button_length": 0,
            "fg_color": [muted, muted],
            "progress_color": [ad0, ad1],
            "button_color": [ac0, ac1],
            "button_hover_color": [ad0, ad1],
        },
        "CTkOptionMenu": {
            "corner_radius": 6,
            "fg_color": [p0, p1],
            "button_color": [ad0, ad1],
            "button_hover_color": [primary, primary],
            "text_color": [btn_text, btn_text],
            "text_color_disabled": [muted, muted],
        },
        "CTkComboBox": {
            "corner_radius": 6,
            "border_width": 2,
            "fg_color": [s0, s1],
            "border_color": [muted, muted],
            "button_color": [muted, muted],
            "button_hover_color": [ad0, ad1],
            "text_color": [t0, t1],
            "text_color_disabled": [muted, muted],
        },
        "CTkScrollbar": {
            "corner_radius": 1000,
            "border_spacing": 4,
            "fg_color": "transparent",
            "button_color": [muted, muted],
            "button_hover_color": [ac0, ac1],
        },
        "CTkSegmentedButton": {
            "corner_radius": 6,
            "border_width": 2,
            "fg_color": [bg_alt, bg_alt],
            "selected_color": [p0, p1],
            "selected_hover_color": [ad0, ad1],
            "unselected_color": [bg_alt, bg_alt],
            "unselected_hover_color": [mid if dark_ui else accent_light, mid if dark_ui else accent_light],
            "text_color": [t0, t1],
            "text_color_disabled": [muted, muted],
        },
        "CTkTextbox": {
            "corner_radius": 6,
            "border_width": 0,
            "fg_color": [s0, s1],
            "border_color": [muted, muted],
            "text_color": [t0, t1],
            "scrollbar_button_color": [muted, muted],
            "scrollbar_button_hover_color": [ac0, ac1],
        },
        "CTkScrollableFrame": {"label_fg_color": [bg_alt, bg_alt]},
        "DropdownMenu": {
            "fg_color": [s0, s1],
            "hover_color": [primary if dark_ui else accent_light, primary if dark_ui else accent_light],
            "text_color": [t0, t1],
        },
        "CTkFont": {
            "macOS": {"family": "SF Display", "size": 13, "weight": "normal"},
            "Windows": {"family": "Segoe UI", "size": 13, "weight": "normal"},
            "Linux": {"family": "Roboto", "size": 13, "weight": "normal"},
        },
    }


def _is_dark_hex(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return True
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000 < 140


def _palette_from_mobile(spec: dict[str, Any], json_path: str) -> ThemePalette:
    c = spec["c"]
    dark_ui = bool(spec["dark_ui"])
    appearance = "Dark" if dark_ui else "Light"
    bg, alt, surface = c["background"], c["backgroundAlt"], c["surface"]
    text, muted = c["text"], c["textMuted"]
    primary, mid = c["primary"], c["primaryMid"]
    accent, accent_dark = c["accent"], c["accentDark"]
    accent_light, chip = c["accentLight"], c["chip"]
    chip_active = c["chipActive"]
    left_panel = c.get("leftPanel") or (accent_light if not dark_ui else alt)
    bubble_sel = c.get("bubbleSel") or (accent_light if not dark_ui else chip)
    source_hover = c.get("sourceHover") or (chip if not dark_ui else mid)
    on_btn = c["textOnDark"] if _is_dark_hex(primary) else text

    def both(x: str) -> tuple[str, str]:
        return (x, x)

    return ThemePalette(
        id=spec["id"],
        label=spec["label"],
        appearance=appearance,
        ctk_theme=json_path,
        window_bg=both(bg),
        left_bg=both(left_panel if not dark_ui else alt),
        mid_bg=both(alt if not dark_ui else bg),
        menubar_bg=both(primary),
        menubar_fg=both(on_btn),
        accent=both(accent),
        accent_hover=both(accent_dark),
        source_row=both(surface if not dark_ui else chip),
        source_active=both(chip if not dark_ui else chip_active),
        source_hover=both(source_hover if not dark_ui else mid),
        bubble=both(surface),
        bubble_unread=both(chip),
        bubble_sel=both(bubble_sel),
        day_bar=both(chip if not dark_ui else mid),
        muted=both(muted),
        text=both(text),
        uj_bg=both(primary),
        uj_fg=both(on_btn),
        reader_bg=bg if dark_ui else alt,
        reader_fg=text,
        primary=both(primary),
        primary_hover=both(mid),
        btn_text=both(on_btn),
        surface=both(surface),
    )


def _peonia_json() -> dict[str, Any]:
    # Élénk rózsa–korall (nem pasztell peónia-klisé)
    return _ctk_from_mobile(
        {
            "background": "#fff5f7",
            "backgroundAlt": "#ffe4ea",
            "surface": "#ffffff",
            "text": "#3f0a1a",
            "textMuted": "#9f5a6c",
            "textOnDark": "#ffffff",
            "primary": "#e11d48",
            "primaryMid": "#be123c",
            "accent": "#fb7185",
            "accentLight": "#fecdd3",
            "accentDark": "#be123c",
            "chip": "#ffe4e6",
            "chipActive": "#e11d48",
        },
        dark_ui=False,
    )


def ensure_theme_files() -> dict[str, str]:
    """JSON fájlok írása / frissítése. Vissza: id → abszolút path."""
    import json

    d = _themes_dir()
    d.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for spec in _MOBILE_THEMES:
        name = f"{spec['id']}.json"
        path = d / name
        data = _ctk_from_mobile(spec["c"], dark_ui=bool(spec["dark_ui"]))
        try:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass
        paths[spec["id"]] = str(path)
    peonia = d / "peonia.json"
    try:
        peonia.write_text(json.dumps(_peonia_json(), indent=2), encoding="utf-8")
    except OSError:
        pass
    paths["peonia"] = str(peonia)
    light_json = d / "light.json"
    try:
        light_json.write_text(
            json.dumps(_ctk_from_mobile(_LIGHT_CLASSIC, dark_ui=False), indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
    paths["light"] = str(light_json)
    return paths


def _light_palette(json_path: str) -> ThemePalette:
    c = _LIGHT_CLASSIC
    text, muted = c["text"], c["textMuted"]
    primary, mid = c["primary"], c["primaryMid"]
    accent, accent_dark = c["accent"], c["accentDark"]
    accent_light, chip = c["accentLight"], c["chip"]
    on_btn = c["textOnDark"]
    return ThemePalette(
        id="light",
        label="Világos",
        appearance="Light",
        ctk_theme=json_path,
        window_bg=_pair(c["background"], c["background"]),
        left_bg=_pair(accent_light, accent_light),
        mid_bg=_pair(c["backgroundAlt"], c["backgroundAlt"]),
        menubar_bg=_pair(primary, primary),
        menubar_fg=_pair(on_btn, on_btn),
        accent=_pair(accent, accent),
        accent_hover=_pair(accent_dark, accent_dark),
        source_row=_pair(c["surface"], c["surface"]),
        source_active=_pair(chip, chip),
        source_hover=_pair(c["backgroundAlt"], c["backgroundAlt"]),
        bubble=_pair(c["surface"], c["surface"]),
        bubble_unread=_pair(chip, chip),
        bubble_sel=_pair(c["backgroundAlt"], c["backgroundAlt"]),
        day_bar=_pair(c["backgroundAlt"], c["backgroundAlt"]),
        muted=_pair(muted, muted),
        text=_pair(text, text),
        uj_bg=_pair(primary, primary),
        uj_fg=_pair(on_btn, on_btn),
        reader_bg=c["backgroundAlt"],
        reader_fg=text,
        primary=_pair(primary, primary),
        primary_hover=_pair(mid, mid),
        btn_text=_pair(on_btn, on_btn),
        surface=_pair(c["surface"], c["surface"]),
    )


def _default_light_dark() -> dict[str, ThemePalette]:
    """Sötét + ideiglenes világos (felülírja _palettes a light.json path-tal)."""
    return {
        "light": _light_palette("blue"),
        "dark": ThemePalette(
            id="dark",
            label="Sötét",
            appearance="Dark",
            ctk_theme="blue",
            window_bg=_pair("#202124", "#202124"),
            left_bg=_pair("#2d2e30", "#2d2e30"),
            mid_bg=_pair("#202124", "#202124"),
            menubar_bg=_pair("#303134", "#303134"),
            menubar_fg=_pair("#e8eaed", "#e8eaed"),
            accent=_pair("#8ab4f8", "#8ab4f8"),
            accent_hover=_pair("#aecbfa", "#aecbfa"),
            source_row=_pair("#303134", "#303134"),
            source_active=_pair("#3c4043", "#3c4043"),
            source_hover=_pair("#35363a", "#35363a"),
            bubble=_pair("#303134", "#303134"),
            bubble_unread=_pair("#3c4043", "#3c4043"),
            bubble_sel=_pair("#414347", "#414347"),
            day_bar=_pair("#2d2e30", "#2d2e30"),
            muted=_pair("#9aa0a6", "#9aa0a6"),
            text=_pair("#e8eaed", "#e8eaed"),
            uj_bg=_pair("#669df6", "#669df6"),
            uj_fg=_pair("#202124", "#202124"),
            reader_bg="#202124",
            reader_fg="#e8eaed",
            primary=_pair("#669df6", "#669df6"),
            primary_hover=_pair("#8ab4f8", "#8ab4f8"),
            btn_text=_pair("#202124", "#202124"),
            surface=_pair("#303134", "#303134"),
        ),
    }


def _palettes() -> dict[str, ThemePalette]:
    paths = ensure_theme_files()
    out = _default_light_dark()
    out["light"] = _light_palette(paths["light"])
    for spec in _MOBILE_THEMES:
        tid = spec["id"]
        out[tid] = _palette_from_mobile(spec, paths[tid])
    out["peonia"] = ThemePalette(
        id="peonia",
        label="Peónia",
        appearance="Light",
        ctk_theme=paths["peonia"],
        window_bg=_pair("#fff5f7", "#fff5f7"),
        left_bg=_pair("#fecdd3", "#fecdd3"),
        mid_bg=_pair("#fff5f7", "#fff5f7"),
        menubar_bg=_pair("#e11d48", "#e11d48"),
        menubar_fg=_pair("#FFFFFF", "#FFFFFF"),
        accent=_pair("#fb7185", "#fb7185"),
        accent_hover=_pair("#be123c", "#be123c"),
        source_row=_pair("#ffffff", "#ffffff"),
        source_active=_pair("#fecdd3", "#fecdd3"),
        source_hover=_pair("#ffe4e6", "#ffe4e6"),
        bubble=_pair("#ffffff", "#ffffff"),
        bubble_unread=_pair("#ffe4e6", "#ffe4e6"),
        bubble_sel=_pair("#fecdd3", "#fecdd3"),
        day_bar=_pair("#ffe4e6", "#ffe4e6"),
        muted=_pair("#9f5a6c", "#9f5a6c"),
        text=_pair("#3f0a1a", "#3f0a1a"),
        uj_bg=_pair("#e11d48", "#e11d48"),
        uj_fg=_pair("#FFFFFF", "#FFFFFF"),
        reader_bg="#fff5f7",
        reader_fg="#3f0a1a",
        primary=_pair("#e11d48", "#e11d48"),
        primary_hover=_pair("#be123c", "#be123c"),
        btn_text=_pair("#FFFFFF", "#FFFFFF"),
        surface=_pair("#FFFFFF", "#FFFFFF"),
    )
    return out


_CACHE: Optional[dict[str, ThemePalette]] = None


def all_themes() -> dict[str, ThemePalette]:
    global _CACHE
    if _CACHE is None:
        _CACHE = _palettes()
    return _CACHE


def clear_theme_cache() -> None:
    global _CACHE
    _CACHE = None


def resolve_theme_id(raw: str | None, *, appearance_fallback: str | None = None) -> str:
    themes = all_themes()
    aliases = {
        "gleam": "light",
        "csillam": "light",
        "muza": "light",
    }
    if raw and raw in aliases:
        raw = aliases[raw]
    if raw and raw in themes:
        return raw
    if appearance_fallback == "Light":
        return "light"
    return "dark"


def get_palette(theme_id: str) -> ThemePalette:
    themes = all_themes()
    tid = resolve_theme_id(theme_id)
    return themes.get(tid) or themes["dark"]


_LAST_CTK_APPLIED: Optional[tuple[str, str]] = None  # (theme_id, appearance)


def apply_ctk_theme(theme_id: str, *, refresh_globals: bool = True) -> ThemePalette:
    """Paletta; induláskor CTk globális téma is (set_appearance_mode villogást okoz)."""
    pal = get_palette(theme_id)
    if not refresh_globals:
        return pal

    import customtkinter as ctk
    from customtkinter.windows.widgets.theme.theme_manager import ThemeManager

    global _LAST_CTK_APPLIED
    prev = _LAST_CTK_APPLIED
    if prev == (pal.id, pal.appearance):
        return pal

    if pal.id == "dark":
        ctk.set_default_color_theme("blue")
    else:
        ctk.set_default_color_theme(pal.ctk_theme)
        try:
            if pal.ctk_theme and pal.ctk_theme != "blue":
                ThemeManager.load_theme(pal.ctk_theme)
        except Exception:
            pass

    if prev is None or prev[1] != pal.appearance:
        ctk.set_appearance_mode(pal.appearance)

    _LAST_CTK_APPLIED = (pal.id, pal.appearance)
    return pal


def style_button_depth(
    btn: Any,
    *,
    fg: str,
    hover: str,
    text: str,
    border_color: str,
    corner_radius: int = 7,
    border_width: int = 1,
) -> None:
    """Közös gomb „kiemelés” — főablak, dialógusok."""
    try:
        btn.configure(
            fg_color=fg,
            hover_color=hover,
            text_color=text,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=border_color,
        )
    except Exception:
        try:
            btn.configure(fg_color=fg, hover_color=hover, text_color=text)
        except Exception:
            pass


def theme_menu_items() -> list[tuple[str, str]]:
    return [(t.id, t.label) for t in all_themes().values()]


def menu_theme_from_palette(pal: ThemePalette):
    """Menüsor / legördülő — ugyanaz a téma paletta (menubar_bg, primary hover)."""
    from app.ctk_menu import MenuTheme

    bar_is_dark = _is_dark_hex(str(pal.menubar_bg[0]))
    popup = pal.day_bar if not bar_is_dark else pal.surface
    win_btn_text = pal.menubar_fg
    return MenuTheme(
        bar_bg=pal.menubar_bg,
        bar_text=pal.menubar_fg,
        popup_bg=popup,
        hover=pal.primary,
        hover_text=pal.btn_text,
        text=pal.text,
        muted=pal.muted,
        border=pal.muted,
        btn_hover=pal.primary_hover if bar_is_dark else pal.source_hover,
        win_btn_text=win_btn_text,
        win_caption_hover=("#E5E5E5", "#3F3F46"),
    )
