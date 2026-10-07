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
    resolve_imap,
    supported_providers_summary,
)
from app.paths import CONFIG_PATH


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
        self.title("Levelező fiókok (IMAP)")
        from app.window_util import center_window
        center_window(self, 720, 920)
        self.minsize(520, 760)
        self._on_saved = on_saved
        self._selected_id: Optional[str] = None
        self._help_url = PROVIDERS_BY_KEY["gmail"].help_url

        self.transient(master)
        self.grab_set()
        self.focus_force()

        ctk.CTkLabel(
            self,
            text=(
                "IMAP fiókok — mint Thunderbirdben. Több fiók is felvehető; "
                "a „Most ellenőriz” mindegyiken végigmegy.\n"
                f"Előre kitöltve: {supported_providers_summary()}, vagy egyéni szerver.\n"
                "Sok helyen alkalmazásjelszó kell (nem a sima bejelentkezési jelszó). "
                "ProtonMail nem támogatott."
            ),
            justify="left",
            anchor="w",
            wraplength=560,
        ).pack(fill="x", padx=16, pady=(16, 8))

        self.help_btn = ctk.CTkButton(
            self,
            text="Súgó / jelszó oldal…",
            command=self._open_help,
        )
        self.help_btn.pack(anchor="w", padx=16, pady=(0, 8))

        # Görgethető tartalom (lista + form)
        scroll_container = ctk.CTkScrollableFrame(self)
        scroll_container.pack(fill="both", expand=True, padx=0, pady=0)
        scroll_container.grid_columnconfigure(0, weight=1)

        self.list_frame = ctk.CTkScrollableFrame(scroll_container, height=120)
        self.list_frame.pack(fill="x", padx=16, pady=(8, 12))

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

        ctk.CTkLabel(form, text="Hitelesítés módja").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.auth_method_var = ctk.StringVar(value="Normál jelszó")
        self.auth_method_menu = ctk.CTkOptionMenu(
            form,
            values=["Normál jelszó", "OAuth2"],
            variable=self.auth_method_var,
            command=self._on_auth_change,
        )
        self.auth_method_menu.grid(row=3, column=1, sticky="ew", padx=8, pady=4)

        self.lbl_password = ctk.CTkLabel(form, text="Jelszó / alkalmazásjelszó")
        self.lbl_password.grid(row=4, column=0, sticky="w", padx=8, pady=4)
        self.entry_password = ctk.CTkEntry(form, placeholder_text="xxxx xxxx xxxx xxxx", show="*")
        self.entry_password.grid(row=4, column=1, sticky="ew", padx=8, pady=4)
        self.password_hint = ctk.CTkLabel(
            form,
            text="Outlook/Gmail: gyakran 16 karakteres alkalmazásjelszó (2FA után).",
            anchor="w",
            text_color=("gray40", "gray65"),
            wraplength=420,
            font=("Segoe UI", 11),
        )
        self.password_hint.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 4))

        self.lbl_oauth = ctk.CTkLabel(form, text="OAuth hozzáférés token")
        self.lbl_oauth.grid(row=6, column=0, sticky="w", padx=8, pady=4)
        self.entry_oauth_token = ctk.CTkEntry(
            form, placeholder_text="Hosszú Bearer token (OAuth2 bejelentkezés után)"
        )
        self.entry_oauth_token.grid(row=6, column=1, sticky="ew", padx=8, pady=4)

        self.lbl_oauth_refresh = ctk.CTkLabel(form, text="OAuth refresh token")
        self.lbl_oauth_refresh.grid(row=7, column=0, sticky="w", padx=8, pady=4)
        self.entry_oauth_refresh = ctk.CTkEntry(
            form, placeholder_text="Opcionális — token megújításhoz"
        )
        self.entry_oauth_refresh.grid(row=7, column=1, sticky="ew", padx=8, pady=4)

        self.oauth_hint = ctk.CTkLabel(
            form,
            text=(
                "Thunderbird OAuth2: a 2FA kódot (SMS/e-mail) a böngészős bejelentkezésnél add meg — "
                "nem IMAP mező. Ide OAuth access token kerül, vagy használd a Normál jelszót + app jelszót."
            ),
            anchor="w",
            text_color=("gray40", "gray65"),
            wraplength=420,
            justify="left",
            font=("Segoe UI", 11),
        )
        self.oauth_hint.grid(row=8, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 4))

        self.oauth_btn = ctk.CTkButton(
            form,
            text="Microsoft OAuth bejelentkezés (eszközkód)…",
            command=self._microsoft_oauth_login,
        )
        self.oauth_btn.grid(row=9, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        self.lbl_ms_client = ctk.CTkLabel(form, text="Azure app ID (OAuth)")
        self.lbl_ms_client.grid(row=10, column=0, sticky="w", padx=8, pady=4)
        self.entry_ms_client = ctk.CTkEntry(
            form, placeholder_text="Application (client) ID — egyszer, minden Outlook fiókhoz"
        )
        self.entry_ms_client.grid(row=10, column=1, sticky="ew", padx=8, pady=4)
        from app.oauth2_outlook import microsoft_client_id

        cid = microsoft_client_id()
        if cid:
            self.entry_ms_client.insert(0, cid)

        ctk.CTkLabel(form, text="IMAP szerver").grid(row=11, column=0, sticky="w", padx=8, pady=4)
        self.entry_host = ctk.CTkEntry(form, placeholder_text="imap.pelda.hu")
        self.entry_host.grid(row=11, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(form, text="IMAP port").grid(row=12, column=0, sticky="w", padx=8, pady=4)
        self.entry_port = ctk.CTkEntry(form, placeholder_text="993", width=80)
        self.entry_port.grid(row=12, column=1, sticky="w", padx=8, pady=4)
        self.entry_port.insert(0, "993")

        self.provider_hint = ctk.CTkLabel(
            form,
            text=PROVIDERS_BY_KEY["gmail"].hint,
            anchor="w",
            text_color=("gray40", "gray65"),
            wraplength=420,
            justify="left",
        )
        self.provider_hint.grid(row=13, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 8))

        self.auth_method_var.set("Normál jelszó")

        # Fix gombok az ablak alján (nem görgethető)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(row, text="Hozzáadás", command=self._start_new_account).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Mentés", command=self._save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row, text="Törlés", fg_color="#8B3A3A", hover_color="#6E2E2E", command=self._delete
        ).pack(side="left")

        self.hint = ctk.CTkLabel(self, text=f"Mentés ide: {CONFIG_PATH}", anchor="w", wraplength=560)
        self.hint.pack(fill="x", padx=16, pady=(0, 12))

        self._apply_provider_fields(PROVIDERS_BY_KEY["gmail"].key)
        self._on_auth_change()
        self._reload_list()

    def _provider_key(self) -> str:
        return LABEL_TO_KEY.get(self.provider_var.get(), "custom")

    def _on_provider_change(self, _label: str | None = None) -> None:
        self._apply_provider_fields(self._provider_key())

    def _on_auth_change(self, method: str | None = None) -> None:
        """Normál jelszó vs OAuth2 — Thunderbird-szerű (IMAP-hez releváns mezők)."""
        m = (method or self.auth_method_var.get() or "Normál jelszó").lower()
        is_oauth = "oauth" in m

        def _show(row_widgets: tuple, show: bool) -> None:
            for w in row_widgets:
                if show:
                    w.grid()
                else:
                    w.grid_remove()

        _show(
            (self.lbl_password, self.entry_password, self.password_hint),
            not is_oauth,
        )
        oauth_widgets = (
            self.lbl_oauth,
            self.entry_oauth_token,
            self.lbl_oauth_refresh,
            self.entry_oauth_refresh,
            self.oauth_hint,
            self.oauth_btn,
            self.lbl_ms_client,
            self.entry_ms_client,
        )
        _show(oauth_widgets, is_oauth)
        if is_oauth:
            self.oauth_hint.configure(
                text=(
                    "Outlook: a sima jelszó gyakran tiltott (Basic auth). "
                    "OAuth2 → eszközkód a microsoft.com/devicelogin oldalon (2FA ott). "
                    "Azure app ID egyszer kell (ingyenes regisztráció)."
                )
            )
        if not is_oauth:
            self.password_hint.configure(
                text="Outlook/Gmail: gyakran 16 karakteres alkalmazásjelszó (2FA után)."
            )

    def _apply_provider_fields(self, key: str) -> None:
        preset = PROVIDERS_BY_KEY.get(key) or PROVIDERS_BY_KEY["custom"]
        self._help_url = preset.help_url
        self.provider_hint.configure(text=preset.hint or "")
        custom = key == "custom"
        if not custom and preset.host:
            self.entry_host.configure(state="normal")
            self.entry_host.delete(0, "end")
            self.entry_host.insert(0, preset.host)
            self.entry_host.configure(state="disabled")
            self.entry_port.configure(state="normal")
            self.entry_port.delete(0, "end")
            self.entry_port.insert(0, str(preset.port))
            self.entry_port.configure(state="disabled")
        else:
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
            host = acc.get("imap_host") or ""
            auth_m = str(acc.get("auth_method") or "password").lower()
            is_oauth = "oauth" in auth_m
            pwd_ok = bool((acc.get("app_password") or "").strip()) and not str(
                acc.get("app_password")
            ).startswith("xxxx")
            tok_ok = bool((acc.get("oauth_token") or "").strip())
            cred_ok = tok_ok if is_oauth else pwd_ok
            auth_tag = "OAuth2" if is_oauth else "jelszó"
            status = (
                "OK"
                if cred_ok and "@" in email and "SAJAT@" not in email.upper()
                else "hiányos"
            )
            text = f"{label}\n{email}  ·  {prov}  ·  {auth_tag}  ·  {host}  ·  {status}"
            
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
            
            ctk.CTkButton(
                row,
                text="🗑",
                width=32,
                height=48,
                font=("Segoe UI", 12),
                fg_color="#8B3A3A",
                hover_color="#6E2E2E",
                command=lambda a=acc: self._delete_account(a),
            ).pack(side="left", padx=(4, 0))

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

        if "oauth" in auth_m:
            self.auth_method_var.set("OAuth2")
        else:
            self.auth_method_var.set("Normál jelszó")
        self._on_auth_change()
        
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
        self.auth_method_var.set("Normál jelszó")
        self.provider_var.set(PROVIDERS_BY_KEY["gmail"].label)
        self._apply_provider_fields("gmail")
        self._on_auth_change()

    def _save(self) -> None:
        label = self.entry_label.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()
        oauth_token = self.entry_oauth_token.get().strip()
        oauth_refresh = self.entry_oauth_refresh.get().strip()
        provider = self._provider_key()
        host = self.entry_host.get().strip()
        port_raw = self.entry_port.get().strip() or "993"
        auth_method = (self.auth_method_var.get() or "Normál jelszó").lower()

        if not email or "@" not in email:
            msg = "❌ Adj meg érvényes e-mail címet!"
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self.after(3000, lambda: self.hint.configure(text=f"Mentés ide: {CONFIG_PATH}", text_color=("gray40", "gray65")))
            return

        is_oauth = "oauth" in auth_method
        if is_oauth:
            if len(oauth_token) < 20:
                msg = "❌ OAuth2: add meg a hozzáférés tokent (hosszú Bearer string)."
                self.hint.configure(text=msg, text_color="#FF6B6B")
                self.after(
                    3000,
                    lambda: self.hint.configure(
                        text=f"Mentés ide: {CONFIG_PATH}", text_color=("gray40", "gray65")
                    ),
                )
                return
        elif not password or len(password.replace(" ", "")) < 8:
            msg = "❌ Normál jelszó: alkalmazásjelszó vagy jelszó kötelező (min. 8 karakter)."
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self.after(3000, lambda: self.hint.configure(text=f"Mentés ide: {CONFIG_PATH}", text_color=("gray40", "gray65")))
            return
        try:
            port = int(port_raw)
        except ValueError:
            msg = "❌ Az IMAP port legyen szám (általában 993)."
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self.after(3000, lambda: self.hint.configure(text=f"Mentés ide: {CONFIG_PATH}", text_color=("gray40", "gray65")))
            return
        if provider == "custom" and not host:
            msg = "❌ Egyéni IMAP-nál add meg a szervert (host)."
            self.hint.configure(text=msg, text_color="#FF6B6B")
            self.after(3000, lambda: self.hint.configure(text=f"Mentés ide: {CONFIG_PATH}", text_color=("gray40", "gray65")))
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

        ms_cid = self.entry_ms_client.get().strip()
        if ms_cid:
            cfg["microsoft_oauth_client_id"] = ms_cid

        cfg["accounts"] = accounts
        save_config(cfg)
        msg = f"✅ Mentve: {email} → {host}:{port}"
        self.hint.configure(text=msg, text_color="#6BCB77")
        self._reload_list()
        if self._on_saved:
            self._on_saved()
        self.after(3000, lambda: self.hint.configure(text=f"Mentés ide: {CONFIG_PATH}", text_color=("gray40", "gray65")))

    def _microsoft_oauth_login(self) -> None:
        import threading

        from app.oauth2_outlook import run_device_login, set_microsoft_client_id

        email = self.entry_email.get().strip()
        if not email or "@" not in email:
            self.hint.configure(text="Előbb add meg az Outlook e-mail címet.")
            return

        cid = self.entry_ms_client.get().strip()
        if not cid:
            self.hint.configure(text="Add meg az Azure Application (client) ID-t.")
            return
        set_microsoft_client_id(cid)
        self.auth_method_var.set("OAuth2")
        self._on_auth_change()

        dlg = ctk.CTkToplevel(self)
        dlg.title("Microsoft OAuth")
        dlg.geometry("480x220")
        dlg.transient(self)
        dlg.grab_set()
        from app.window_util import center_window

        center_window(dlg, 480, 220)
        status_lbl = ctk.CTkLabel(dlg, text="Indul…", wraplength=440, justify="left")
        status_lbl.pack(fill="both", expand=True, padx=16, pady=16)

        def set_status(msg: str) -> None:
            self.after(0, lambda: status_lbl.configure(text=msg))

        def work() -> None:
            try:
                tok = run_device_login(on_status=set_status)
            except Exception as exc:
                self.after(0, lambda: status_lbl.configure(text=str(exc)))
                return
            if not tok:
                return

            def done() -> None:
                self.entry_oauth_token.delete(0, "end")
                self.entry_oauth_token.insert(0, tok.get("access_token") or "")
                self.entry_oauth_refresh.delete(0, "end")
                self.entry_oauth_refresh.insert(0, tok.get("refresh_token") or "")
                self.hint.configure(
                    text="OAuth token megvan — kattints a Mentés gombra.",
                    text_color="#6BCB77",
                )
                dlg.destroy()

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
        
        ctk.CTkButton(btn_row, text="Törlés", fg_color="#8B3A3A", hover_color="#6E2E2E", command=confirm_delete).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Mégse", command=dlg.destroy).pack(side="left", padx=4)
