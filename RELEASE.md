# Release — Hírlevél követő

## Build (Windows, fejlesztői gép)

1. Tálca → **Kilépés** (ne fusson régi `HirlevelKoveto.exe`).
2. **`BUILD-ZIP.cmd`** — exe + `dist_release\HirlevelKoveto-{verzió}-win64.zip`.
3. **`program\HirlevelKoveto.exe --version`** — ellenőrizd a verziót és időbélyeget.

Alternatíva csak exe: **`BUILD-EXE.cmd`**. Telepítő (opcionális, aláírás nélkül): **`BUILD-INSTALLER.cmd`**.

## GitHub Release

- Melléklet: **`dist_release\HirlevelKoveto-1.0.x-win64.zip`** (egy fájl).
- Forrás: tag **`v1.0.x`** ugyanarra a commitra, amiről buildeltél.
- Másold be / frissítsd a **Release notes** sablont (lent).

## Letöltőnek (rövid szöveg Release-hez)

- Csomagold ki a zipet bárhova, indítsd a **HirlevelKoveto.exe** fájlt.
- Windows **ismeretlen kiadó** figyelmeztetés: *További információ* → *Futtatás mégis* (nincs code signing).
- Levelek és beállítások: **`%LOCALAPPDATA%\HirlevelKoveto`** — a zip mappa mozgatható, az adatok maradnak.
- **ProtonMail:** hivatalosan nem támogatott.
- **Outlook:** *Bejelentkezés Microsoft-fiókkal* a fiók ablakban (beépített OAuth client ID; opcionális saját ID: `config.json` → `microsoft_oauth_client_id`).

## Füstteszt (build után, ~15 perc)

- [ ] Indulás, **Fontos tudnivalók** (első alkalommal)
- [ ] **Súgó → Jogi Dokumentumok Központ**, Használati útmutató, A Programról
- [ ] **Levelező fiókok** + Kapcsolatteszt (Gmail vagy Outlook)
- [ ] **Most ellenőriz**, levél olvasó
- [ ] **Fájl → Mentés…** (zip backup)

## Aktuális build (fejlesztői gép)

- **Verzió:** `1.0.3` (build **3**) — `program\HirlevelKoveto.exe --version`
- **Zip:** `dist_release\HirlevelKoveto-1.0.3-win64.zip`

## Release notes sablon

```markdown
## Hírlevél követő 1.0.{build}

**Letöltés:** `HirlevelKoveto-1.0.{build}-win64.zip` — csomagold ki, futtasd a HirlevelKoveto.exe fájlt.

### Fontos
- Nincs aláírt telepítő; Windows figyelmeztethet ismeretlen kiadóra.
- Adatok: %LOCALAPPDATA%\HirlevelKoveto
- ProtonMail nem támogatott.

### Változások
- …
```
