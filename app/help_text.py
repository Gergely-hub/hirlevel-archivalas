"""Felhasználói súgó- és tájékoztató szövegek (nem fejlesztői)."""

from __future__ import annotations

APP_NAME = "Hírlevél követő"
APP_VERSION = "1.0"

try:
    from app.build_info import BUILD_NUMBER as _BUILD_NUMBER
    from app.build_info import BUILD_STAMP as _BUILD_STAMP
    from app.build_info import VERSION_LABEL as _VERSION_LABEL
except ImportError:
    _BUILD_NUMBER = 0
    _BUILD_STAMP = "dev"
    _VERSION_LABEL = APP_VERSION

NEVJEGY = f"""{APP_NAME}
Verzió: {_VERSION_LABEL}
Build szám: {_BUILD_NUMBER}
Időbélyeg: {_BUILD_STAMP}

Hírlevelek helyi archívuma a leveleződből.
A levelek a gépeden maradnak; a program nem küldi el őket harmadik félnek.

Bezárás (X): a program a tálcán tovább fut.
Teljes kilépés: Fájl → Kilépés, vagy a tálca menü → Kilépés.
"""

SÚGÓ_ROVID = """Indítás
• Indítsd a Hírlevél követőt (INDITAS.cmd, a program mappából az exe, vagy az asztali parancsikon).
• Ha „már fut” üzenetet kapsz: nézd a tálcát (óra mellett), ott megnyithatod vagy kiléphetsz.

Levelező fiók
• Levelezés → Levelező fiókok… — szolgáltató (Gmail, Outlook, Yahoo, iCloud,
  Freemail, Citromail, Vipmail) vagy Egyéni / más szolgáltató.
  Proton: kísérleti (Bridge) profil — lásd lent.
• Több fiók is felvehető; a „Most ellenőriz” mindegyiken végigmegy.
• Gmail, Yahoo, iCloud, magyar szolgáltatók: jelszó vagy alkalmazásjelszó
  (Alkalmazásjelszó készítése gomb a fiók űrlapon).
• Outlook / Hotmail: „Bejelentkezés Microsoft-fiókkal” — a program elmenti a tokent.
• ProtonMail (proton.me): kísérleti — Proton Mail Bridge kell (127.0.0.1:1143, Bridge jelszó).
  Nincs garancia.
• Levelezés → Most ellenőriz — új levelek.
• Levelezés → Régebbi levelek betöltése… — múltbeli hírlevelek (lassú, ritkán).

Hírlevelek (bal oldal)
• + Új hírlevél — feladó e-mail címe (forrás).
• Címke — csoportosítás; Elrejtés — listából kiveszi (Elrejtettek… alatt vissza).
• Törlés… — forrás + helyi levelek; Helyi levelek törlése… — csak a levelek.
• 🔄 a forrás során — csak az adott forrás szinkronja.

Olvasás és keresés
• Középen a lista, jobbra a formázott levél.
• Szűrők: Összes / Olvasatlan / Kedvenc, dátumtól.
• Keresés felül; forrás kiválasztása bal oldalon tallózáshoz.

Export
• Egy levél: Word / PDF a buborékon vagy az olvasóban.
• Több levél: Word lista / PDF lista (középső lista fejlécében).

Biztonsági mentés (kézi)
• Fájl → Mentés… — utolsó mentés mappájába, új időbélyeges zip.
• Fájl → Mentés másként… — mappa és fájlnév választása.
• Fájl → Backup visszaállítás… — zip-ből visszaállítás.
• Nincs automatikus háttérmentés.

Beállítások
• Frissítési intervallum — milyen gyakran ellenőrizd a leveleket (nem backup).
• Téma, Windows indításkor induljon.

Súgó és jogi szövegek
• Használati útmutató… — részletes leírás.
• Jogi Dokumentumok Központ… — adatkezelés, biztonság, feltételek (fülök).
• Hibabejelentő… — hibajelzés böngészőben.
"""

MENTES_BIZTONSAG = """Mit tartalmaz a biztonsági mentés?
A mentés egy tömörített fájl (zip), benne az archívumod és a beállítások.
A beállításokban lehetnek a levelező fiók adatai (például alkalmazásjelszó).

Gépre mentés
A zip a választott mappába kerül (Mentés… az utolsó mappába, Mentés másként… bárhova).
Ezt a mappát te őrzöd (lemez, USB, stb.). A program nem tárol adatot online.

Visszaállítás
Fájl → Backup visszaállítás… — zip kiválasztása, majd felülírja a jelenlegi archívumot.
A régi fájlok .pre-restore időbélyeggel átnevezve maradnak.

Fontos
• A mentési fájlt kezelj bizalmasan (jelszó lehet benne).
• Ne oszd meg másokkal, és ne töltsd nyilvános helyre.
• Teljes kilépés előtt ellenőrizd, hogy a mentés sikeres volt-e.
"""

FONTOS_TUDNIVALOK = """Üdvözöl a Hírlevél követő!

Helyi program
• A levelek és beállítások a gépeden maradnak (AppData\\Local\\HirlevelKoveto).
• A program a levelező szerverről tölt le (IMAP); központi szolgáltatás nincs.

Biztonság
• A levelező jelszó vagy Outlook-token a config.json fájlban van, titkosítás nélkül.
• Gmailnél érdemes alkalmazásjelszót használni (korlátozott, visszavonható).
• Erős Windows-jelszó és opcionális BitLocker ajánlott.

Helyi tárolás és biztonsági másolat
• A szinkronizált levelek és beállítások folyamatosan a helyi adatbázisba kerülnek.
• Külön zip biztonsági másolatot csak te indíthatod: Fájl → Mentés… / Mentés másként… (nincs automatikus háttérmentés).

Részletes jogi és adatvédelmi szövegek
Súgó → Jogi Dokumentumok Központ…
"""

ADATKEZELES = """Adatkezelés röviden

Helyi feldolgozás
• A levelek és beállítások az AppData\\Local\\HirlevelKoveto mappában (nem az interneten).
• A program a levelező szerverről olvassa a hírleveleket (titkosított kapcsolat).
• A program a levelező szerverről tölt; adataid a gépeden maradnak.

Adataid
• Levelező jelszó / Outlook token: config.json, NEM titkosítva
  → Ahol lehet: alkalmazásjelszó (korlátozott, visszavonható)
  → Erős Windows-jelszó + BitLocker ajánlott
• Levelek: SQLite adatbázis (data\\hirlevelek.db), helyben
• Zip biztonsági másolat: csak kézzel (Fájl → Mentés… / Mentés másként…); a levelek szinkronkor automatikusan a helyi DB-be kerülnek

Gyakorlati jogok a programban
• Megtekintés: levelek, források a főablakban
• Export: Word / PDF; teljes archívum: zip mentés
• Törlés: levél (buborék), forrás (Törlés…), fiók (Levelező fiókok… → Törlés)
• Helyesbítés: forrás szerkesztése (✎), címke, fiók adatok mentése

Teljes jogi szöveg
Súgó → Jogi Dokumentumok Központ… → Adatkezelés fül
(vagy a telepítési mappa / Hivatalos HTML fájlok).
"""

ADATVEDELEM_TELJES = """GDPR és Adatvédelem

Ez az alkalmazás helyi feldolgozást nyújt.
Minden adat az Ön gépén marad. A program a készítő felé nem küld használati adatot.

Adatkezelő: ÖN (saját gépén)
Feldolgozandó adatok: levelező jelszó/token, levelek, beállítások
Megőrzés: az Ön döntése (törlés, export, zip mentés)
Az Ön jogai: hozzáférés, helyesbítés, törlés, adathordozhatóság
Panasz: NAIH (naih.hu)

Biztonsági kockázatok
• Jelszavak titkosítás nélkül a config.json-ban
• Ajánlott: alkalmazásjelszó + BitLocker + erős Windows-jelszó

Részletes tájékoztatók
Súgó → Jogi Dokumentumok Központ…
"""
