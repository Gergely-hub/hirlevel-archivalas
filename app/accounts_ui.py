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
            }
        )
    return out


class AccountsWindow(ctk.CTkToplevel):
    def __init__(self, master: Any, on_saved: Optional[Callable[[], None]] = None) -> None:
        super().__init__(master)
        self.title("Levelező fiókok (IMAP)")
        self.geometry("620x640")
        self.minsize(520, 560)
        self._on_saved = on_saved
        self._selected_id: Optional[str] = None
        self._help_url = PROVIDERS_BY_KEY["gmail"].help_url

        self.transient(master)
        self.grab_set()
        self.focus_force()

        ctk.CTkLabel(
            self,
            text="IMAP fiókok — mint Thunderbirdben: szolgáltató vagy egyéni szerver.\n"
            "Sok helyen alkalmazásjelszó kell (nem a sima bejelentkezési jelszó).",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        self.help_btn = ctk.CTkButton(
            self,
            text="Súgó / jelszó oldal…",
            command=self._open_help,
        )
        self.help_btn.pack(anchor="w", padx=16, pady=(0, 8))

        self.list_frame = ctk.CTkScrollableFrame(self, height=120)
        self.list_frame.pack(fill="x", padx=16, pady=8)

        form = ctk.CTkFrame(self)
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

        ctk.CTkLabel(form, text="Jelszó / app jelszó").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.entry_password = ctk.CTkEntry(form, placeholder_text="xxxx xxxx xxxx xxxx", show="*")
        self.entry_password.grid(row=3, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(form, text="IMAP szerver").grid(row=4, column=0, sticky="w", padx=8, pady=4)
        self.entry_host = ctk.CTkEntry(form, placeholder_text="imap.pelda.hu")
        self.entry_host.grid(row=4, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(form, text="IMAP port").grid(row=5, column=0, sticky="w", padx=8, pady=4)
        self.entry_port = ctk.CTkEntry(form, placeholder_text="993", width=80)
        self.entry_port.grid(row=5, column=1, sticky="w", padx=8, pady=4)
        self.entry_port.insert(0, "993")

        self.provider_hint = ctk.CTkLabel(
            form,
            text=PROVIDERS_BY_KEY["gmail"].hint,
            anchor="w",
            text_color=("gray40", "gray65"),
            wraplength=420,
            justify="left",
        )
        self.provider_hint.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 8))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(row, text="Mentés / hozzáadás", command=self._save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Új üres űrlap", command=self._clear_form).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row, text="Törlés", fg_color="#8B3A3A", hover_color="#6E2E2E", command=self._delete
        ).pack(side="left")

        self.hint = ctk.CTkLabel(self, text=f"Mentés ide: {CONFIG_PATH}", anchor="w", wraplength=560)
        self.hint.pack(fill="x", padx=16, pady=(4, 12))

        self._apply_provider_fields(PROVIDERS_BY_KEY["gmail"].key)
        self._reload_list()

    def _provider_key(self) -> str:
        return LABEL_TO_KEY.get(self.provider_var.get(), "custom")

    def _on_provider_change(self, _label: str | None = None) -> None:
        self._apply_provider_fields(self._provider_key())

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
            pwd_ok = bool((acc.get("app_password") or "").strip()) and not str(
                acc.get("app_password")
            ).startswith("xxxx")
            status = "OK" if pwd_ok and "@" in email and "SAJAT@" not in email.upper() else "hiányos"
            text = f"{label}\n{email}  ·  {prov}  ·  {host}  ·  {status}"
            ctk.CTkButton(
                self.list_frame,
                text=text,
                anchor="w",
                height=52,
                fg_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray35"),
                command=lambda a=acc: self._load_into_form(a),
            ).pack(fill="x", pady=3)

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
        if key == "custom":
            self.entry_host.configure(state="normal")
            self.entry_host.delete(0, "end")
            self.entry_host.insert(0, str(acc.get("imap_host") or ""))
            self.entry_port.configure(state="normal")
            self.entry_port.delete(0, "end")
            self.entry_port.insert(0, str(acc.get("imap_port") or 993))

    def _clear_form(self) -> None:
        self._selected_id = None
        self.entry_label.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.provider_var.set(PROVIDERS_BY_KEY["gmail"].label)
        self._apply_provider_fields("gmail")

    def _save(self) -> None:
        label = self.entry_label.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()
        provider = self._provider_key()
        host = self.entry_host.get().strip()
        port_raw = self.entry_port.get().strip() or "993"

        if not email or "@" not in email:
            self.hint.configure(text="Adj meg érvényes e-mail címet.")
            return
        if not password or len(password.replace(" ", "")) < 8:
            self.hint.configure(text="A jelszó / alkalmazásjelszó hiányzik vagy túl rövid.")
            return
        try:
            port = int(port_raw)
        except ValueError:
            self.hint.configure(text="Az IMAP port legyen szám (általában 993).")
            return
        if provider == "custom" and not host:
            self.hint.configure(text="Egyéni IMAP-nál add meg a szervert (host).")
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
            "app_password": password,
            "provider": provider,
            "imap_host": host,
            "imap_port": port,
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
        self.hint.configure(text=f"Mentve: {email} → {host}:{port}")
        self._reload_list()
        if self._on_saved:
            self._on_saved()

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
