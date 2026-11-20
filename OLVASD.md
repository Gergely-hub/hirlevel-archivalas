# Hírlevél követő — használati útmutató

## Indítás

**Letöltés:** a **`HirlevelKoveto-…-win64.zip`** csomagot csomagold ki egy mappába (pl. `D:\Programok\HirlevelKoveto`), majd indítsd a **`HirlevelKoveto.exe`** fájlt. Nincs aláírt telepítő — a Windows **ismeretlen kiadó** figyelmeztetésnél: *További információ* → *Futtatás mégis*. A levelek továbbra is a `%LOCALAPPDATA%\HirlevelKoveto` mappában vannak (nem a zip mappájában).

Ha azt írja, hogy már fut: nézd a **tálcát** (az óra mellett). Ott megnyithatod; kilépés: tálca menü → **Kilépés**.

Az ablak **X** gombja nem állítja le a programot — a tálcán tovább fut. Teljes kilépés: **Fájl → Kilépés** vagy tálca → **Kilépés**.

---

## Első beállítás

1. **Levelezés → Levelező fiókok…**  
   Válassz szolgáltatót (Gmail, Outlook, Yahoo, iCloud, Freemail, Citromail, Vipmail)
   vagy **Egyéni / más szolgáltató**, add meg az e-mailt és a jelszót / alkalmazásjelszót.  
   Több fiók is felvehető. **ProtonMail:** opcionálisan **kísérleti (Bridge)** profil — lásd lent.
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
**Bejelentkezés Microsoft-fiókkal** — sima jelszó általában nem elég.

**ProtonMail?**  
**Kísérleti (Bridge):** telepítsd és indítsd a [Proton Mail Bridge](https://proton.me/mail/bridge) programot.  
A fiók ablakban válaszd: **ProtonMail — kísérleti (Bridge)** (`127.0.0.1`, port `1143`, Bridge által generált jelszó).  
Kísérleti funkció — nincs garancia; visszajelzés örömmel fogadott.

**Az olvasó üres?**  
Próbáld a buborékon a **Teljes szöveg** gombot, vagy **Régebbi levelek betöltése…**.

**Hol vannak az adataim?**  
`%LOCALAPPDATA%\HirlevelKoveto` (config, adatbázis).

---

## Adatvédelem és jogi szövegek

A programban: **Súgó → Jogi Dokumentumok Központ…** (Adatkezelés, Biztonság, Feltételek, Licenc fülök).

Ugyanezek az exe melletti **Hivatalos** mappában **HTML** formában is elérhetők.

**Röviden:** A levelek és beállítások a gépeden maradnak. Erős Windows-jelszó és BitLocker ajánlott; Gmailnál alkalmazásjelszó.

**Hibajelzés:** **Súgó → Hibabejelentő…**
