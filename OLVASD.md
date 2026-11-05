# Hírlevél követő — használati útmutató

## Indítás

**Letöltés (GitHub Release):** a **`HirlevelKoveto-…-win64.zip`** csomagot csomagold ki egy mappába (pl. `D:\Programok\HirlevelKoveto`), majd indítsd a **`HirlevelKoveto.exe`** fájlt. Nincs aláírt telepítő — a Windows **ismeretlen kiadó** figyelmeztetésnél: *További információ* → *Futtatás mégis*. A levelek továbbra is a `%LOCALAPPDATA%\HirlevelKoveto` mappában vannak (nem a zip mappájában).

**Fejlesztés:** **INDITAS.cmd**, vagy a `program` mappában az exe, vagy az asztali **Hírlevél követő (Python)** parancsikon.

Ha azt írja, hogy már fut: nézd a **tálcát** (az óra mellett). Ott megnyithatod; kilépés: tálca menü → **Kilépés**.

Az ablak **X** gombja nem állítja le a programot — a tálcán tovább fut. Teljes kilépés: **Fájl → Kilépés** vagy tálca → **Kilépés**.

---

## Első beállítás

1. **Levelezés → Levelező fiókok…**  
   Válassz szolgáltatót (Gmail, Outlook, Yahoo, iCloud, Freemail, Citromail, Vipmail)
   vagy **Egyéni / más szolgáltató**, add meg az e-mailt és a jelszót / alkalmazásjelszót.  
   Több fiók is felvehető. **ProtonMail nem támogatott.**
2. **Most ellenőriz** — behúzza az új hírleveleket (minden beállított fiókról).
3. Bal oldalon **+ Új hírlevél** — feladó e-mail címe (forrás).

---

## Használat

| Hol | Mit csinál |
|-----|------------|
| Bal oszlop | Hírlevelek listája, címkék, elrejtés, 🔄 forrás szinkron |
| Közép | Levelek előnézete, szűrők, Word / PDF / törlés |
| Jobb | Formázott olvasó, linkek, böngészőben megnyitás |

**Elrejtés** vs **Törlés:** az elrejtés visszaállítható (**Elrejtettek…**); a törlés végleges a helyi archívumból
(a levelező fiókban a levelek megmaradnak — új szinkron visszahozhatja őket).

**Szűrők:** Összes · Olvasatlan · Kedvenc · dátumtól (ÉÉÉÉ-HH-NN).

**Keresés:** a felső mezőben. Forrás kiválasztása bal oldalon tallózáshoz.

---

## Mentés (Word, PDF, backup)

- **Egy levél:** buborék vagy olvasó → Word / PDF.
- **Lista:** **Word lista** / **PDF lista** — ami éppen a középső listában van.
- **Biztonsági mentés (zip):** **Fájl → Mentés…** (utolsó mappa) vagy **Mentés másként…**
- **Visszaállítás:** **Fájl → Backup visszaállítás…**

A zip tartalmazhatja a levelező beállításokat is — **ne oszd meg** másokkal. Nincs automatikus háttérmentés.

---

## Gyakori kérdések

**Nem jönnek a levelek?**  
Ellenőrizd a fiókot és az alkalmazásjelszót. **Most ellenőriz**, vagy **Levelezés → Régebbi levelek betöltése…** (első alkalommal).

**Outlook?**  
**Bejelentkezés Microsoft-fiókkal** — sima jelszó általában nem elég. A program alapból beépített OAuth client ID-t használ; haladóknak opcionális saját Azure app: `config.json` → `microsoft_oauth_client_id`.

**Release / build:** lásd [RELEASE.md](RELEASE.md) (zip készítés, GitHub Release, füstteszt).

**ProtonMail?**  
Hivatalosan **nem támogatott** — nincs garantált működés, hibajelzést ehhez nem kezelünk.

**Az olvasó üres?**  
Próbáld a buborékon a **Teljes szöveg** gombot, vagy **Régebbi levelek betöltése…**.

**Hol vannak az adataim?**  
`%LOCALAPPDATA%\HirlevelKoveto` (config, adatbázis).

---

## Adatvédelem és jogi szövegek

A programban: **Súgó → Jogi Dokumentumok Központ…** (Adatkezelés, Biztonság, Feltételek, Licenc fülök).

Forrás / fejlesztői mappában ugyanezek **HTML** és **MD** fájlokban is (pl. `Hivatalos` mappa az exe mellett).

**Röviden:** Helyi feldolgozás, nincs telemetria. Erős Windows-jelszó és BitLocker ajánlott; Gmailnál alkalmazásjelszó.

**Hibajelzés:** **Súgó → Hibabejelentő…**
