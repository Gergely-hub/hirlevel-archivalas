# Hírlevél követő — használati útmutató

## Indítás

Futtasd az **INDITAS** parancsfájlt, vagy a `program` mappában a **HirlevelKoveto** programot.

Ha azt írja, hogy már fut: nézd a **tálcát** (az óra mellett). Ott jobb klikkel megnyithatod vagy kiléphetsz.

Az ablak **X** gombja nem állítja le a programot — a tálcán tovább fut. Teljes kilépés: **Fájl → Kilépés** vagy tálca → **Kilépés**.

---

## Első beállítás

1. **Levelezés → Levelező fiókok…**  
   Válassz szolgáltatót (Gmail, Outlook, Yahoo, iCloud, Freemail, Citromail, Vipmail)
   vagy **Egyéni IMAP**, add meg az e-mailt és az **alkalmazásjelszót**
   (sok helyen ez nem a szokásos bejelentkezési jelszó).  
   Több fiók is felvehető. **ProtonMail nem támogatott.**
2. **Most ellenőriz** — behúzza az új hírleveleket (minden beállított fiókról).
3. Bal oldalon válassz egy küldőt, vagy **+ Új hírlevél**.

---

## Használat

| Hol | Mit csinál |
|-----|------------|
| Bal oszlop | Hírlevelek listája, címkék, elrejtés |
| Közép | Levelek előnézete, szűrők, Word / PDF / törlés |
| Jobb | Formázott olvasó, linkek, böngészőben megnyitás |

**Elrejtés** vs **Törlés:** az elrejtés visszaállítható; a törlés végleges a helyi archívumból
(a Gmail / egyéb fiókban a levelek megmaradnak — új szinkron visszahoztathatja őket).

**Szűrők:** Összes · Olvasatlan · Kedvenc · dátumtól (ÉÉÉÉ-HH-NN).

**Keresés:** a felső mezőben. „Csak a kiválasztottban” = csak az aktuális hírlevélben.

---

## Mentés (Word, PDF, backup)

- **Egy levél:** buborék vagy olvasó → Word / PDF (a formázott, képes nézet).
- **Lista:** Word lista / PDF lista — ami éppen a középső listában van.
- **Biztonsági mentés:** Fájl → Mentés biztonsági másolat… → mappát választasz.

A biztonsági mentés tartalmazhatja a levelező beállításokat is — **ne oszd meg** másokkal.

Visszaállítás: **Fájl → Visszaállítás backupból…**

---

## Gyakori kérdések

**Nem jönnek a levelek?**  
Ellenőrizd a fiókot, a szolgáltatót és az alkalmazásjelszót. Próbáld: Most ellenőriz, majd Teljes előzmény import.

**Másik szolgáltató (nem Gmail)?**  
Ugyanott: Levelező fiókok → szolgáltató vagy Egyéni IMAP. A szinkron IMAP-pal megy, mint Thunderbirdben.

**ProtonMail?**  
Nincs támogatva (nincs sima IMAP Bridge nélkül).

**Az olvasó sötét / nehezen olvasható?**  
A levelek világos „papír” háttéren jelennek meg. Ha üres: Teljes szöveg a buborékon, vagy teljes import.

**Antivirus / Norton figyelmeztetés?**  
Vedd kivételnek a program mappáját, majd indítsd újra.

**Hol vannak az adataim?**  
A saját felhasználói mappádban, a Windows alatt:  
`AppData\Local\HirlevelKoveto`  
(ide íródik az archívum és a beállítás).

---

## Adatvédelem és Jogi Dokumentumok

A csomagban az alábbi dokumentumok találhatók:

- **ADATKEZELESI_TAJEKOZTATO.md** — GDPR-kompatibilis adatkezelési tájékoztató
  + Kezelt adatok köre, tárolás helye, az Ön jogai (hozzáférés, törlés, adathordozhatóság)
  + Biztonsági kockázatok és ajánlások

- **BIZTONSAG_ES_ADATVEDELEM.md** — Biztonsági nyilatkozat
  + Az IMAP-jelszó titkosítása (vagy hiánya)
  + Lemez titkosítés (BitLocker) ajánlása
  + Biztonsági ellenőrzési lista

- **FELHASZNALASI_FELTETELEK.md** — Felhasználási feltételek és EULA
  + A program „AS IS" (ahogy van) kerül felkínálásra, garanciavállalás nélkül
  + Felelősség korlátozása, jogos használat, tiltott tevékenységek

- **LICENSE.md** — MIT-licenc
  + Nyílt forráskódú licenc: szabadon használható, módosítható, terjeszthető
  + A szerzői jogi nyilatkozatot meg kell őrizni

**Röviden:** Az alkalmazás 100%-ban helyi feldolgozást nyújt. Az Ön adatai a gépén maradnak, nincs telemetria vagy központi szerver. A biztonsag az Ön operációs rendszer biztonságára támaszkodik.

**Biztonsagi javaslat:** Használjon alkalmazásjelszót (pl. Gmail-nál), és erősen ajánlott a BitLocker-lemezt titkosítás.
