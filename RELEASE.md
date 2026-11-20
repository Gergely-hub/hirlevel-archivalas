# Release — Hírlevél követő

## Build (Windows, fejlesztői gép)

1. Tálca → **Kilépés** (ne fusson régi `HirlevelKoveto.exe`).
2. **`BUILD-ZIP.cmd`** — exe + `dist_release\HirlevelKoveto-{verzió}-win64.zip`.
3. **`program\HirlevelKoveto.exe --version`** — ellenőrizd a verziót és időbélyeget.

Alternatíva csak exe: **`BUILD-EXE.cmd`**. Telepítő (opcionális, aláírás nélkül): **`BUILD-INSTALLER.cmd`**.

## GitHub Release (nyilvános letöltés)

- **Repó:** `Gergely-hub/hirlevel-koveto` (csak README, OLVASD, kép + zip — nincs app forrás).
- Melléklet: **`dist_release\HirlevelKoveto-1.0.x-win64.zip`**
- Példa: `gh release upload v1.0.5 dist_release\HirlevelKoveto-1.0.5-win64.zip --repo Gergely-hub/hirlevel-koveto --clobber`
- Forráskód: **privát** `hirlevel-archivalas` (ez a mappa).

## Letöltőnek (rövid szöveg Release-hez)

- Csomagold ki a zipet bárhova, indítsd a **HirlevelKoveto.exe** fájlt.
- Windows **ismeretlen kiadó** figyelmeztetés: *További információ* → *Futtatás mégis* (nincs code signing).
- Levelek és beállítások: **`%LOCALAPPDATA%\HirlevelKoveto`** — a zip mappa mozgatható, az adatok maradnak.
- **ProtonMail:** kísérleti — Bridge kell (`127.0.0.1:1143`); nincs garancia.
- **Outlook:** *Bejelentkezés Microsoft-fiókkal* a fiók ablakban (beépített OAuth client ID; opcionális saját ID: `config.json` → `microsoft_oauth_client_id`).

## Füstteszt (build után, ~15 perc)

- [ ] Indulás, **Fontos tudnivalók** (első alkalommal)
- [ ] **Súgó → Jogi Dokumentumok Központ**, Használati útmutató, A Programról
- [ ] **Levelező fiókok** + Kapcsolatteszt (Gmail vagy Outlook)
- [ ] **Most ellenőriz**, levél olvasó
- [ ] **Fájl → Mentés…** (zip backup)

## Aktuális build (fejlesztői gép)

- **Verzió:** `1.0.5` (build **5**) — `program\HirlevelKoveto.exe --version`
- **Zip:** `dist_release\HirlevelKoveto-1.0.5-win64.zip`
- Build parancs (egy futás): `QUICK-BUILD.cmd` vagy asztali `BUILD-HIRLEVEL.cmd` (Norton: `NORTON-BUILD.md`)

## Release notes sablon

```markdown
## Hírlevél követő 1.0.{build}

**Letöltés:** `HirlevelKoveto-1.0.{build}-win64.zip` — csomagold ki, futtasd a HirlevelKoveto.exe fájlt.

### Fontos
- Nincs aláírt telepítő; Windows figyelmeztethet ismeretlen kiadóra.
- Adatok: %LOCALAPPDATA%\HirlevelKoveto
- ProtonMail kísérleti (Bridge); nincs garancia.

### Változások
- Proton Mail — kísérleti (Bridge) profil; localhost IMAP STARTTLS (Bridge 1143)
- README + OLVASD.md a zip csomagban; GitHub Releases letöltési link
```

## Közzététel (checklist)

- [ ] `BUILD-ZIP.cmd` → friss zip
- [ ] Füstteszt (`RELEASE.md` „Füstteszt”)
- [ ] Commit + push `master`
- [ ] Tag `v{VERSION_LABEL}` ugyanarra a commitra
- [ ] GitHub Release: zip asset + notes (fenti sablon)
- [ ] Közzétételi link: `https://github.com/Gergely-hub/hirlevel-koveto/releases/latest` (nyilvános, forrás nélkül)
