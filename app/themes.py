from __future__ import annotations

"""UI színsémák — Világos/Sötét/Kávé + egyedi hangulatú témák
(Múzsa, Friss reggel, Éjfél, Óceán, Tompa papír, Peónia).
"""

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


# --- Egyedi hangulatú témák (ne hasonlítsanak egymásra / Kávéra) ---
# Világos / Sötét / Kávé érintetlen — lent csak a többi.

_MOBILE_THEMES: list[dict[str, Any]] = [
    {
        # Lila–ibolya, kreatív / modern
        "id": "muza",
        "label": "Múzsa",
        "dark_ui": False,
        "c": {
            "background": "#f6f3fc",
            "backgroundAlt": "#ebe4f7",
            "surface": "#ffffff",
            "text": "#1a1230",
            "textMuted": "#6f648a",
            "textOnDark": "#f8f5ff",
            "primary": "#6d28d9",
            "primaryMid": "#5b21b6",
            "accent": "#a78bfa",
            "accentLight": "#ddd6fe",
            "accentDark": "#5b21b6",
            "chip": "#ede9fe",
            "chipActive": "#6d28d9",
        },
    },
    {
        # Élénk menta–zöld, reggeli frissesség
        "id": "frissReggel",
        "label": "Friss reggel",
        "dark_ui": False,
        "c": {
            "background": "#f1faf4",
            "backgroundAlt": "#dff3e8",
            "surface": "#ffffff",
            "text": "#0f2419",
            "textMuted": "#4d6b5a",
            "textOnDark": "#f0fdf4",
            "primary": "#15803d",
            "primaryMid": "#166534",
            "accent": "#4ade80",
            "accentLight": "#bbf7d0",
            "accentDark": "#166534",
            "chip": "#dcfce7",
            "chipActive": "#15803d",
        },
    },
    {
        # Hideg éjkék + égőkék (nem bordó!)
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
            "accentDark": "#1e40af",
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
        # Élénk ég–cián, tengerpart
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
            "primary": "#0e7490",
            "primaryMid": "#155e75",
            "accent": "#22d3ee",
            "accentLight": "#a5f3fc",
            "accentDark": "#155e75",
            "chip": "#cffafe",
            "chipActive": "#0e7490",
        },
    },
    {
        # Hideg zsálya–kő, minimal
        "id": "tompaPapir",
        "label": "Tompa papír",
        "dark_ui": False,
        "c": {
            "background": "#f3f5f2",
            "backgroundAlt": "#e4e9e3",
            "surface": "#fbfcfb",
            "text": "#1c2420",
            "textMuted": "#5f6b64",
            "textOnDark": "#f4f7f5",
            "primary": "#3d4f46",
            "primaryMid": "#2f3d36",
            "accent": "#84a98c",
            "accentLight": "#cad2c5",
            "accentDark": "#52796f",
            "chip": "#dde5df",
            "chipActive": "#3d4f46",
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
            "corner_radius": 6,
            "border_width": 0,
            "fg_color": [p0, p1],
            "hover_color": [ad0, ad1],
            "border_color": [muted, muted],
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
            "border_width_checked": 6,
            "border_width_unchecked": 3,
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
    on_btn = c["textOnDark"] if _is_dark_hex(primary) else text

    def both(x: str) -> tuple[str, str]:
        return (x, x)

    return ThemePalette(
        id=spec["id"],
        label=spec["label"],
        appearance=appearance,
        ctk_theme=json_path,
        # Asztalon erősebb jel: menü = primary, bal = accentLight (ne majdnem fehér)
        window_bg=both(bg),
        left_bg=both(accent_light if not dark_ui else alt),
        # Középső is láthatóan témás (ne csak gombok)
        mid_bg=both(alt if not dark_ui else bg),
        menubar_bg=both(primary),
        menubar_fg=both(on_btn),
        accent=both(accent),
        accent_hover=both(accent_dark),
        source_row=both(surface if not dark_ui else chip),
        source_active=both(chip if not dark_ui else chip_active),
        source_hover=both(chip if not dark_ui else mid),
        bubble=both(surface),
        bubble_unread=both(chip),
        bubble_sel=both(accent_light),
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
    return paths


def _default_light_dark() -> dict[str, ThemePalette]:
    """Tiszta kék–szürke — mindkét CTk-slot ugyanaz (ne keveredjen Light/Dark fél)."""
    return {
        "light": ThemePalette(
            id="light",
            label="Világos",
            appearance="Light",
            ctk_theme="blue",
            window_bg=_pair("#EBEBEB", "#EBEBEB"),
            left_bg=_pair("#E0E0E0", "#E0E0E0"),
            mid_bg=_pair("#F2F2F2", "#F2F2F2"),
            menubar_bg=_pair("#D5D5D5", "#D5D5D5"),
            menubar_fg=_pair("#1A1A1A", "#1A1A1A"),
            accent=_pair("#2F6FED", "#2F6FED"),
            accent_hover=_pair("#2558C0", "#2558C0"),
            source_row=_pair("#E8E8E8", "#E8E8E8"),
            source_active=_pair("#D5E4F7", "#D5E4F7"),
            source_hover=_pair("#D0D0D0", "#D0D0D0"),
            bubble=_pair("#E4E8EE", "#E4E8EE"),
            bubble_unread=_pair("#E8F0FC", "#E8F0FC"),
            bubble_sel=_pair("#C9DBF2", "#C9DBF2"),
            day_bar=_pair("#C5D0DC", "#C5D0DC"),
            muted=_pair("#5A5A5A", "#5A5A5A"),
            text=_pair("#1A1A1A", "#1A1A1A"),
            uj_bg=_pair("#2F6FED", "#2F6FED"),
            uj_fg=_pair("#FFFFFF", "#FFFFFF"),
            reader_bg="#f6f7f9",
            reader_fg="#1a1a1a",
            primary=_pair("#3B8ED0", "#3B8ED0"),
            primary_hover=_pair("#36719F", "#36719F"),
            btn_text=_pair("#FFFFFF", "#FFFFFF"),
            surface=_pair("#FAFAFA", "#FAFAFA"),
        ),
        "dark": ThemePalette(
            id="dark",
            label="Sötét",
            appearance="Dark",
            ctk_theme="blue",
            window_bg=_pair("#242424", "#242424"),
            left_bg=_pair("#2B2B2B", "#2B2B2B"),
            mid_bg=_pair("#1E1E1E", "#1E1E1E"),
            menubar_bg=_pair("#2B2B2B", "#2B2B2B"),
            menubar_fg=_pair("#F0F0F0", "#F0F0F0"),
            accent=_pair("#6CB6FF", "#6CB6FF"),
            accent_hover=_pair("#5AA0E8", "#5AA0E8"),
            source_row=_pair("#333333", "#333333"),
            source_active=_pair("#3A4A5E", "#3A4A5E"),
            source_hover=_pair("#404040", "#404040"),
            bubble=_pair("#2A2A2A", "#2A2A2A"),
            bubble_unread=_pair("#3A4A5E", "#3A4A5E"),
            bubble_sel=_pair("#3A4554", "#3A4554"),
            day_bar=_pair("#333840", "#333840"),
            muted=_pair("#A0A0A0", "#A0A0A0"),
            text=_pair("#F0F2F5", "#F0F2F5"),
            uj_bg=_pair("#3D7FE0", "#3D7FE0"),
            uj_fg=_pair("#FFFFFF", "#FFFFFF"),
            reader_bg="#1a1c20",
            reader_fg="#e8eaed",
            primary=_pair("#1F6AA5", "#1F6AA5"),
            primary_hover=_pair("#144870", "#144870"),
            btn_text=_pair("#DCE4EE", "#DCE4EE"),
            surface=_pair("#2B2B2B", "#2B2B2B"),
        ),
    }


def _palettes() -> dict[str, ThemePalette]:
    paths = ensure_theme_files()
    out = _default_light_dark()
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


def apply_ctk_theme(theme_id: str) -> ThemePalette:
    """appearance + CTk színfájl. Világos/Sötét: beépített kék, többi: JSON."""
    import customtkinter as ctk
    from customtkinter.windows.widgets.theme.theme_manager import ThemeManager

    clear_theme_cache()
    ensure_theme_files()
    pal = get_palette(theme_id)
    # Először a témafájl, aztán az appearance — ne maradjon előző séma
    if pal.id in ("light", "dark"):
        ctk.set_default_color_theme("blue")
    else:
        ctk.set_default_color_theme(pal.ctk_theme)
    ctk.set_appearance_mode(pal.appearance)
    # ThemeManager cache: biztosan az aktuális fájl legyen betöltve
    try:
        if pal.id not in ("light", "dark") and pal.ctk_theme:
            ThemeManager.load_theme(pal.ctk_theme)
    except Exception:
        pass
    return pal


def theme_menu_items() -> list[tuple[str, str]]:
    return [(t.id, t.label) for t in all_themes().values()]


def menu_theme_from_palette(pal: ThemePalette):
    """CTk menüsáv / legördülő színei a palettából (ne mindig szürke/fehér)."""
    from app.ctk_menu import MenuTheme

    bar_is_dark = _is_dark_hex(str(pal.menubar_bg[0]))
    # Legördülő: világos témánál day_bar, sötétnél surface — ne keveredjen idegen séma
    popup = pal.day_bar if not bar_is_dark else pal.surface
    # Ablakgombok: Win11 semleges hover, ikon szín = menüsáv szöveg
    if bar_is_dark:
        win_btn_text = pal.menubar_fg
        win_caption_hover = ("#E5E5E5", "#3F3F46")
    else:
        win_btn_text = pal.menubar_fg
        win_caption_hover = ("#E5E5E5", "#3F3F46")
    return MenuTheme(
        bar_bg=pal.menubar_bg,
        bar_text=pal.menubar_fg,
        popup_bg=popup,
        hover=pal.primary,
        hover_text=pal.btn_text,
        text=pal.text,
        muted=pal.muted,
        border=pal.primary,
        btn_hover=pal.primary_hover if bar_is_dark else pal.source_hover,
        win_btn_text=win_btn_text,
        win_caption_hover=win_caption_hover,
    )
