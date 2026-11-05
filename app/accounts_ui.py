from __future__ import annotations

import re
import webbrowser
from typing import Any, Callable, Optional

import customtkinter as ctk

from app.db import load_config, save_config
from app.imap_providers import (
    LABEL_TO_KEY,
    PROVIDER_LABELS,
    PROVIDERS_BY_KEY,
    guess_provider_key,
    provider_label,
    provider_uses_microsoft_oauth,
    resolve_imap,
)
from app.themes import get_palette, resolve_theme_id, style_button_depth


def _slug_id(email: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (email or "").lower()).strip("-")
    return base or "fiok"


def raw_accounts(cfg: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    cfg = cfg or load_config()
    out: list[dict[str, Any]] = []
    for raw in cfg.get("accounts") or []:
        if not isinstance(raw, dict):
            continue
        provider = str(raw.get("provider") or "gmail").strip().lower() or "gmail"
        host, port = resolve_imap(
            provider,
            imap_host=str(raw.get("imap_host") or ""),
            imap_port=raw.get("imap_port"),
        )
        out.append(
            {
                "id": str(raw.get("id") or ""),
                "label": str(raw.get("label") or ""),
                "email": str(raw.get("email") or ""),
                "app_password": str(raw.get("app_password") or ""),
                "provider": provider,
                "imap_host": host,
                "imap_port": port,
                "auth_method": str(raw.get("auth_method") or "password"),
                "oauth_token": str(raw.get("oauth_token") or ""),
                "oauth_refresh_token": str(raw.get("oauth_refresh_token") or ""),
            }
        )
    return out


class AccountsWindow(ctk.CTkToplevel):
    def __init__(self, master: Any, on_saved: Optional[Callable[[], None]] = None) -> None:
        super().__init__(master)
        self.title("Levelező fiókok")
        from app.window_util import center_window
        center_window(self, 680, 780)
        self.minsize(520, 640)
        self._on_saved = on_saved
        self._selected_id: Optional[str] = None
        self._oauth_login_busy = False
        self._help_url = PROVIDERS_BY_KEY["gmail"].help_url

        self.transient(master)
        self.grab_set()
        self.focus_force()

        # Görgethető tartalom (lista + form)
        scroll_container = ctk.CTkScrollableFrame(self)
        scroll_container.pack(fill="both", expand=True, padx=0, pady=0)
        scroll_container.grid_columnconfigure(0, weight=1)

        self.list_frame = ctk.CTkScrollableFrame(scroll_container, height=120)
        self.list_frame.pack(fill="x", padx=16, pady=(16, 12))

        form = ctk.CTkFrame(scroll_container)
        form.pack(fill="x", padx=16, pady=8)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Megjelenített név").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.entry_label = ctk.CTkEntry(form, placeholder_text="pl. Fő fiók")
        self.entry_label.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(form, text="Szolgáltató").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.provider_var = ctk.StringVar(value=PROVIDERS_BY_KEY["gmail"].label)
        self.provider_menu = ctk.CTkOptionMenu(
            form,
            values=PROVIDER_LABELS,
            variable=self.provider_var,
            command=self._on_provider_change,
        )
        self.provider_menu.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(form, text="E-mail").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.entry_email = ctk.CTkEntry(form, placeholder_text="te@pelda.hu")
        self.entry_email.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        self.entry_email.bind("<FocusOut>", self._guess_from_email)

        self.lbl_password = ctk.CTkLabel(form, text="Jelszó / alkalmazásjelszó")
        self.lbl_password.grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.entry_password = ctk.CTkEntry(form, placeholder_text="xxxx xxxx xxxx xxxx", show="*")
        self.entry_password.grid(row=3, column=1, sticky="ew", padx=8, pady=4)
        self.password_hint = ctk.CTkLabel(
            form,
            text="",
            anchor="w",
            text_color=("gray40", "gray65"),
            wraplength=420,
            font=("Segoe UI", 11),
        )
        self.password_hint.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 4))

        self.lbl_imap_host = ctk.CTkLabel(form, text="Levelező szerver")
        self.lbl_imap_host.grid(row=5, column=0, sticky="w", padx=8, pady=4)
        self.entry_host = ctk.CTkEntry(form, placeholder_text="imap.pelda.hu")
        self.entry_host.grid(row=5, column=1, sticky="ew", padx=8, pady=4)

        self.lbl_imap_port = ctk.CTkLabel(form, text="Port")
        self.lbl_imap_port.grid(row=6, column=0, sticky="w", padx=8, pady=4)
        self.entry_port = ctk.CTkEntry(form, placeholder_text="993", width=80)
        self.entry_port.grid(row=6, column=1, sticky="w", padx=8, pady=4)
        self.entry_port.insert(0, "993")

        self.oauth_btn = ctk.CTkButton(
            form,
            text="Bejelentkezés Microsoft-fiókkal",
            height=40,
            command=self._microsoft_oauth_login,
        )
        self.oauth_btn.grid(row=7, column=0, columnspan=2, sticky="ew", padx=8, pady=8)

        self.app_password_help_btn = ctk.CTkButton(
            form,
            text="Alkalmazásjelszó készítése (böngészőben)…",
            fg_color="transparent",
            border_width=1,
            text_color=("#1a5fb4", "#62a0ea"),
            command=self._open_help,
        )
        self.app_password_help_btn.grid(row=8, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))

        self.test_btn = ctk.CTkButton(
            form,
            text="Kapcsolat tesztelése",
            fg_color="transparent",
            border_width=1,
            text_color=("#1a5fb4", "#62a0ea"),
            command=self._test_connection,
        )
        self.test_btn.grid(row=9, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 8))

        self.auth_method_var = ctk.StringVar(value="Normál jelszó")
        self.entry_oauth_token = ctk.CTkEntry(form)
        self.entry_oauth_refresh = ctk.CTkEntry(form)

        footer = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray92", "gray17"))
        footer.pack(side="bottom", fill="x")

        ctk.CTkFrame(footer, height=1, fg_color=("gray78", "gray28")).pack(fill="x")

        footer_inner = ctk.CTkFrame(footer, fg_color="transparent")
        footer_inner.pack(fill="x", padx=16, pady=(14, 16))

        self.hint = ctk.CTkLabel(
            footer_inner,
            text="",
            anchor="w",
            wraplength=560,
            text_color=("gray40", "gray65"),
            justify="left",
        )
        self.hint.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(footer_inner, fg_color="transparent")
        row.pack(fill="x")
        self._add_btn = ctk.CTkButton(row, text="Hozzáadás", command=self._start_new_account)
        self._add_btn.pack(side="left", padx=(0, 8))
        self._save_btn = ctk.CTkButton(row, text="Mentés", command=self._save)
        self._save_btn.pack(side="left", padx=(0, 8))
        self._delete_btn = ctk.CTkButton(row, text="Törlés", command=self._delete)
        self._delete_btn.pack(side="left")

        self._apply_provider_fields(PROVIDERS_BY_KEY["gmail"].key)
        self._reload_list()
        self._style_account_buttons()

    def _clear_status_later(self, ms: int = 3500) -> None:
        self.after(
            ms,
            lambda: self.hint.configure(text="", text_color=("gray40", "gray65")),
        )

    def _account_palette(self):
        cfg = load_config()
        tid = resolve_theme_id(str(cfg.get("ui_theme") or ""))
        return get_palette(tid)

    def _style_account_buttons(self) -> None:
        pal = self._account_palette()
        appearance = pal.appearance
        pick = lambda pair: pair[1] if appearance == "Dark" else pair[0]
        fg = pick(pal.primary)
        hover = pick(pal.primary_hover)
        txt = pick(pal.btn_text)
        border = pick(pal.accent_hover)
        for btn in (
            self.oauth_btn,
            self.app_password_help_btn,
            self.test_btn,
            self._add_btn,
            self._save_btn,
        ):
            style_button_depth(
                btn, fg=fg, hover=hover, text=txt, border_color=border
            )
        self._style_delete_button(self._delete_btn)

    def _style_delete_button(self, btn: ctk.CTkButton) -> None:
        pal = self._account_palette()
        appearance = pal.appearance
        pick = lambda pair: pair[1] if appearance == "Dark" else pair[0]
        style_button_depth(
            btn,
            fg=pick(pal.primary_hover),
            hover=pick(pal.accent_hover),
            text=pick(pal.btn_text),
            border_color=pick(pal.accent_hover),
        )

    def _provider_key(self) -> str:
        return LABEL_TO_KEY.get(self.provider_var.get(), "custom")

    def _on_provider_change(self, _label: str | None = None) -> None:
        self._apply_provider_fields(self._provider_key())

    def _form_uses_oauth(self) -> bool:
        return provider_uses_microsoft_oauth(self._provider_key())

    def _account_from_form(self) -> "Account":
        from app.db import Account

        provider = self._provider_key()
        host = self.entry_host.get().strip()
        port_raw = self.entry_port.get().strip() or "993"
        port = int(port_raw)
        host, port = resolve_imap(provider, imap_host=host, imap_port=port)
        is_oauth = self._form_uses_oauth()
        return Account(
            id="test",
            label=(self.entry_label.get().strip() or self.entry_email.get().strip() or "teszt"),
            email=self.entry_email.get().strip(),
            app_password=self.entry_password.get().strip(),
            provider=provider,
            imap_host=host,
            imap_port=port,
            auth_method="oauth2" if is_oauth else "password",
            oauth_token=self.entry_oauth_token.get().strip() or None,
            oauth_refresh_token=self.entry_oauth_refresh.get().strip() or None,
        )

    def _test_connection(self) -> None:
        import threading

        from app.gmail_fetch import test_imap_connection

        email = self.entry_email.get().strip()
        if not email or "@" not in email:
            self.hint.configure(text="Kapcsolatteszthez add meg az e-mail címet.", text_color="#FF6B6B")
            return
        if not self._form_uses_oauth() and len(self.entry_password.get().strip()) < 8:
            self.hint.configure(text="Kapcsolatteszthez add meg a jelszót.", text_color="#FF6B6B")
            return

        self.hint.configure(text="Kapcsolat tesztelése…", text_color=("gray40", "gray65"))
        self.test_btn.configure(state="disabled")

        def work() -> None:
            ok, msg = test_imap_connection(self._account_from_form())

            def done() -> None:
                self.test_btn.configure(state="normal")
                color = "#6BCB77" if ok else "#FF6B6B"
                self.hint.configure(text=msg, text_color=color)

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _apply_provider_fields(self, key: str) -> None:
        preset = PROVIDERS_BY_KEY.get(key) or PROVIDERS_BY_KEY["custom"]
        self._help_url = preset.help_url
        oauth = provider_uses_microsoft_oauth(key)
        custom = key == "custom"

        def _show(widgets: tuple, show: bool) -> None:
            for w in widgets:
                if show:
                    w.grid()
                else:
                    w.grid_remove()

        if oauth:
            self.auth_method_var.set("OAuth2 (haladó)")
        else:
            self.auth_method_var.set("Normál jelszó")

        _show((self.lbl_password, self.entry_password), not oauth)
        self.password_hint.grid_remove()
        _show((self.oauth_btn,), oauth)
        _show((self.app_password_help_btn,), not oauth)
        if not oauth:
            if custom:
                self.app_password_help_btn.configure(
                    text="Levelező beállítások súgója (böngészőben)…"
                )
            else:
                self.app_password_help_btn.configure(
                    text="Alkalmazásjelszó készítése (böngészőben)…"
                )
        _show(
            (self.lbl_imap_host, self.entry_host, self.lbl_imap_port, self.entry_port),
            custom,
        )

        if not custom and preset.host:
            self.entry_host.configure(state="normal")
            self.entry_host.delete(0, "end")
            self.entry_host.insert(0, preset.host)
            self.entry_host.configure(state="disabled")
            self.entry_port.configure(state="normal")
            self.entry_port.delete(0, "end")
            self.entry_port.insert(0, str(preset.port))
            self.entry_port.configure(state="disabled")
        elif custom:
            self.entry_host.configure(state="normal")
            self.entry_port.configure(state="normal")
            if not self.entry_port.get().strip():
                self.entry_port.insert(0, "993")

    def _guess_from_email(self, _event: Any = None) -> None:
        email = self.entry_email.get().strip()
        if not email or "@" not in email:
            return
        # Csak akkor tippelünk, ha új űrlap / nincs kézi custom kitöltés folyamatban
        key = guess_provider_key(email)
        label = provider_label(key)
        if label in PROVIDER_LABELS:
            self.provider_var.set(label)
            self._apply_provider_fields(key)

    def _open_help(self) -> None:
        url = self._help_url or "https://support.mozilla.org/hu/kb/automatic-account-configuration"
        webbrowser.open(url)

    def _reload_list(self) -> None:
        for w in self.list_frame.winfo_children():
            w.destroy()
        accounts = raw_accounts()
        if not accounts:
            ctk.CTkLabel(self.list_frame, text="Még nincs fiók — töltsd ki az űrlapot lent.").pack(
                anchor="w", padx=4, pady=4
            )
            return
        for acc in accounts:
            email = acc["email"] or "(nincs e-mail)"
            label = acc["label"] or email
            prov = provider_label(str(acc.get("provider") or "gmail"))
            auth_m = str(acc.get("auth_method") or "password").lower()
            is_oauth = "oauth" in auth_m
            pwd_ok = bool((acc.get("app_password") or "").strip()) and not str(
                acc.get("app_password")
            ).startswith("xxxx")
            tok_ok = bool((acc.get("oauth_token") or "").strip())
            cred_ok = tok_ok if is_oauth else pwd_ok
            status = (
                "kész"
                if cred_ok and "@" in email and "SAJAT@" not in email.upper()
                else "hiányos"
            )
            text = f"{label}\n{email}  ·  {prov}  ·  {status}"
            
            # Fiók sor: szerkesztés gomb + info + törlés gomb
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            ctk.CTkButton(
                row,
                text="✎",
                width=32,
                height=48,
                font=("Segoe UI", 14),
                command=lambda a=acc: self._load_into_form(a),
            ).pack(side="left", padx=(0, 4))
            
            ctk.CTkButton(
                row,
                text=text,
                anchor="w",
                height=48,
                fg_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray35"),
                command=lambda a=acc: self._load_into_form(a),
            ).pack(side="left", fill="both", expand=True)
            
            trash = ctk.CTkButton(
                row,
                text="🗑",
                width=32,
                height=48,
                font=("Segoe UI", 12),
                command=lambda a=acc: self._delete_account(a),
            )
            trash.pack(side="left", padx=(4, 0))
            self._style_delete_button(trash)

    def _load_into_form(self, acc: dict[str, Any]) -> None:
        self._selected_id = acc.get("id") or None
        self.entry_label.delete(0, "end")
        self.entry_label.insert(0, acc.get("label") or "")
        self.entry_email.delete(0, "end")
        self.entry_email.insert(0, acc.get("email") or "")
        self.entry_password.delete(0, "end")
        self.entry_password.insert(0, acc.get("app_password") or "")

        key = str(acc.get("provider") or "gmail")
        self.provider_var.set(provider_label(key))
        self._apply_provider_fields(key)
        
        # Auth method betöltése
        auth_m = str(acc.get("auth_method") or "password").lower()
        self.entry_oauth_token.delete(0, "end")
        self.entry_oauth_token.insert(0, acc.get("oauth_token") or "")
        self.entry_oauth_refresh.delete(0, "end")
        self.entry_oauth_refresh.insert(0, acc.get("oauth_refresh_token") or "")

        if key == "custom":
            self.entry_host.configure(state="normal")
            self.entry_host.delete(0, "end")
            self.entry_host.insert(0, str(acc.get("imap_host") or ""))
            self.entry_port.configure(state="normal")
            self.entry_port.delete(0, "end")
            self.entry_port.insert(0, str(acc.get("imap_port") or 993))

    def _start_new_account(self) -> None:
        """Hozzáadás: mentés MAJD új fiók (forma törlése)."""
        self._save()
        self._clear_form()

    def _clear_form(self) -> None:
        self._selected_id = None
        self.entry_label.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.entry_oauth_token.delete(0, "end")
        self.entry_oauth_refresh.delete(0, "end")
        self.provider_var.set(PROVIDERS_BY_KEY["gmail"].label)
        self._apply_provider_fields("gmail")

    def _save(self) -> None:
        label = self.entry_label.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()
        oauth_token = self.entry_oauth_token.get().strip()
        oauth_refresh = self.entry_oauth_refresh.get().strip()
        provider = self._provider_key()
        host = self.entry_host.get().strip()
        port_raw = self.entry_port.get().strip() or "993"
        if not email or "@" not in email:
            msg = "❌ Adj meg érvényes e-mail címet!"
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self._clear_status_later()
            return

        is_oauth = provider_uses_microsoft_oauth(provider)
        if is_oauth:
            if len(oauth_token) < 20:
                msg = "❌ Előbb a „Bejelentkezés Microsoft-fiókkal” gomb, majd Mentés."
                self.hint.configure(text=msg, text_color="#FF6B6B")
                self._clear_status_later()
                return
        elif not password or len(password.replace(" ", "")) < 8:
            msg = "❌ Normál jelszó: alkalmazásjelszó vagy jelszó kötelező (min. 8 karakter)."
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self._clear_status_later()
            return
        try:
            port = int(port_raw)
        except ValueError:
            msg = "❌ A port legyen szám (általában 993)."
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self._clear_status_later()
            return
        if provider == "custom" and not host:
            msg = "❌ Egyéni szolgáltatónál add meg a levelező szerver címét."
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self._clear_status_later()
            return
        if not label:
            label = email

        host, port = resolve_imap(provider, imap_host=host, imap_port=port)

        cfg = load_config()
        accounts = list(cfg.get("accounts") or [])
        acc_id = self._selected_id or _slug_id(email)

        payload = {
            "id": acc_id,
            "label": label,
            "email": email,
            "app_password": password if not is_oauth else "",
            "provider": provider,
            "imap_host": host,
            "imap_port": port,
            "auth_method": "oauth2" if is_oauth else "password",
            "oauth_token": oauth_token if is_oauth else "",
            "oauth_refresh_token": oauth_refresh if is_oauth else "",
        }

        updated = False
        for i, raw in enumerate(accounts):
            if not isinstance(raw, dict):
                continue
            rid = str(raw.get("id") or "")
            rem = str(raw.get("email") or "").lower()
            if rid == acc_id or rem == email.lower():
                payload["id"] = rid or acc_id
                accounts[i] = payload
                updated = True
                self._selected_id = payload["id"]
                break

        if not updated:
            accounts.append(payload)
            self._selected_id = acc_id

        cfg["accounts"] = accounts
        save_config(cfg)
        msg = f"✅ Mentve: {label}"
        self.hint.configure(text=msg, text_color="#6BCB77")
        self._reload_list()
        if self._on_saved:
            self._on_saved()
        self._clear_status_later()

    def _microsoft_oauth_login(self) -> None:
        import threading

        from app.oauth2_outlook import run_pkce_login

        if self._oauth_login_busy:
            return
        email = self.entry_email.get().strip()
        if not email or "@" not in email:
            self.hint.configure(text="Előbb add meg az Outlook e-mail címet.")
            return
        if not self._form_uses_oauth():
            self.hint.configure(text="Microsoft bejelentkezés csak Outlook szolgáltatónál.")
            return

        self._oauth_login_busy = True
        try:
            self.oauth_btn.configure(state="disabled")
        except Exception:
            pass

        dlg = ctk.CTkToplevel(self)
        dlg.title("Microsoft bejelentkezés")
        dlg.geometry("480x240")
        dlg.transient(self)
        dlg.grab_set()
        from app.window_util import center_window

        center_window(dlg, 480, 240)
        status_lbl = ctk.CTkLabel(
            dlg,
            text="Indul…",
            wraplength=440,
            justify="left",
            font=("Segoe UI", 12),
        )
        status_lbl.pack(fill="both", expand=True, padx=16, pady=16)

        def set_status(msg: str) -> None:
            self.after(0, lambda: status_lbl.configure(text=msg))

        def release_oauth_ui() -> None:
            self._oauth_login_busy = False
            try:
                self.oauth_btn.configure(state="normal")
            except Exception:
                pass

        def work() -> None:
            try:
                tok = run_pkce_login(email=email, on_status=set_status)
            except Exception as exc:
                self.after(0, lambda: status_lbl.configure(text=str(exc)))
                self.after(0, release_oauth_ui)
                return
            if not tok:
                self.after(0, release_oauth_ui)
                return

            def done() -> None:
                self.entry_oauth_token.delete(0, "end")
                self.entry_oauth_token.insert(0, tok.get("access_token") or "")
                self.entry_oauth_refresh.delete(0, "end")
                self.entry_oauth_refresh.insert(0, tok.get("refresh_token") or "")
                self.hint.configure(
                    text="Bejelentkezés kész — mentés…",
                    text_color="#6BCB77",
                )
                dlg.destroy()
                release_oauth_ui()
                self._save()

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _delete(self) -> None:
        if not self._selected_id and not self.entry_email.get().strip():
            self.hint.configure(text="Válassz fiókot a listából a törléshez.")
            return
        cfg = load_config()
        email = self.entry_email.get().strip().lower()
        acc_id = self._selected_id
        new_accounts = []
        for raw in cfg.get("accounts") or []:
            if not isinstance(raw, dict):
                continue
            if acc_id and str(raw.get("id") or "") == acc_id:
                continue
            if email and str(raw.get("email") or "").lower() == email:
                continue
            new_accounts.append(raw)
        cfg["accounts"] = new_accounts
        save_config(cfg)
        self._clear_form()
        self.hint.configure(text="Fiók törölve.")
        self._reload_list()
        if self._on_saved:
            self._on_saved()

    def _delete_account(self, acc: dict[str, Any]) -> None:
        """Fiók törlése megerősítéssel."""
        email = acc.get("email") or "(nincs e-mail)"
        label = acc.get("label") or email
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Fiók törlése")
        dlg.geometry("400x180")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        
        from app.window_util import center_window
        center_window(dlg, 400, 180)
        
        ctk.CTkLabel(
            dlg,
            text=f"Biztosan törlöd a(z) {label} fiókot?\n{email}",
            justify="center",
            wraplength=360,
        ).pack(padx=16, pady=16)
        
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(padx=16, pady=8)
        
        def confirm_delete() -> None:
            cfg = load_config()
            acc_id = acc.get("id")
            email_lower = (acc.get("email") or "").lower()
            new_accounts = []
            for raw in cfg.get("accounts") or []:
                if not isinstance(raw, dict):
                    continue
                if acc_id and str(raw.get("id") or "") == acc_id:
                    continue
                if email_lower and str(raw.get("email") or "").lower() == email_lower:
                    continue
                new_accounts.append(raw)
            cfg["accounts"] = new_accounts
            save_config(cfg)
            self.hint.configure(text=f"Fiók törölve: {label}")
            self._reload_list()
            self._clear_form()
            dlg.destroy()
            if self._on_saved:
                self._on_saved()
        
        confirm_btn = ctk.CTkButton(btn_row, text="Törlés", command=confirm_delete)
        confirm_btn.pack(side="left", padx=4)
        self._style_delete_button(confirm_btn)
        cancel = ctk.CTkButton(btn_row, text="Mégse", command=dlg.destroy)
        cancel.pack(side="left", padx=4)
        pal = self._account_palette()
        appearance = pal.appearance
        pick = lambda pair: pair[1] if appearance == "Dark" else pair[0]
        style_button_depth(
            cancel,
            fg=pick(pal.source_row),
            hover=pick(pal.source_hover),
            text=pick(pal.text),
            border_color=pick(pal.muted),
        )
