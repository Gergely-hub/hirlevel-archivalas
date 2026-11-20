# Build Norton / antivírus (kivételek)

A **BUILD-ZIP.cmd** / PyInstaller **több ezer fájlt** ír. Norton gyakran **folyam felfedezés (SONAR)** vagy **Python** miatt riaszt — nem feltétlenül a projekt mappa hiánya miatt.

## Amit már jó, ha benne van

- **`D:\Mobilfejlesztes\*`** — lefedi a `hirlevel-gmail-archivalas` mappát is (`program`, `_build_work`, `dist_release`).  
  Ha ez megvan, **nem kell** külön hozzáadni a teljes projekt útvonalát.

## Amit érdemes **még** hozzáadni (+ Hozzáadás → Fájl vagy mappa)

Másolható útvonalak (Explorerbe illeszd, vagy Tallózás):

| Miért | Útvonal |
|--------|---------|
| PyInstaller + pip fut itt | `C:\Users\figye\AppData\Local\Programs\Python\Python313` |
| Ide ír a build közben is | `C:\Users\figye\AppData\Local\Temp` |
| PyInstaller bootloader | `C:\Users\figye\AppData\Local\Programs\Python\Python313\Lib\site-packages\PyInstaller` |

Opcionális (ha továbbra is exe-t quarantínezi):

| Miért | Útvonal |
|--------|---------|
| Kész program | `D:\Mobilfejlesztes\hirlevel-gmail-archivalas\program\HirlevelKoveto.exe` |

**Nem** kell kizárni a `%LOCALAPPDATA%\HirlevelKoveto` mappát (ott a levelek — az maradjon vizsgált).

## Ha még mindig riaszt (kivétel mellett is)

A „Fájl / mappa kivételek” **nem minden** Norton modult kapcsol ki. Build közben:

1. **Felugró riasztásnál:** **Engedélyezés** / **Megbízhatóként jelölés** → válaszd a **python.exe** vagy **HirlevelKoveto.exe** fájlt, és jelöld: **Ne kérdezzen újra ehhez a fájlhoz** (ha van ilyen).
2. Norton → **Beállítások** → keresd: **SONAR** / **Speciális védelem** / **Ismeretlen alkalmazások** — ideiglenesen engedékenyebb, vagy add hozzá a **python.exe**-t a megbízhatókhoz.
3. **Egy** build futásonként — ne indíts 5 BUILD ablakot egyszerre.

## Egy tiszta build

1. Tálca → **Kilépés** (HirlevelKoveto).
2. **Egy** parancs: `QUICK-BUILD.cmd` vagy asztali `BUILD-HIRLEVEL.cmd`.
3. Várj **5–15 percet**.
4. `program\HirlevelKoveto.exe --version`  
   Zip: `dist_release\HirlevelKoveto-1.0.x-win64.zip`
