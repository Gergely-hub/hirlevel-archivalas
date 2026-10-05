"""Felhasználói súgó- és tájékoztató szövegek (nem fejlesztői)."""

from __future__ import annotations

APP_NAME = "Hírlevél követő"
APP_VERSION = "1.0"

try:
    from app.build_info import BUILD_STAMP as _BUILD_STAMP
except ImportError:
    _BUILD_STAMP = "dev"

NEVJEGY = f"""{APP_NAME}
Verzió: {APP_VERSION}
Build: {_BUILD_STAMP}

Hírlevelek helyi archívuma a leveleződből.
A levelek a gépeden maradnak; a program nem küldi el őket harmadik félnek.

Bezárás (X): a program a tálcán tovább fut.
Teljes kilépés: Fájl → Kilépés, vagy a tálca menü → Kilépés.
"""

SÚGÓ_ROVID = """Indítás
• Indítsd a Hírlevél követőt (INDITAS vagy a program ikonja).
• Ha „már fut” üzenetet kapsz: nézd a tálcát (óra mellett), ott megnyithatod.

Levelező fiók (IMAP)
• Levelezés → Levelező fiókok… — szolgáltató választása (Gmail, Outlook, Yahoo,
  iCloud, Freemail, Citromail, Vipmail) vagy egyéni IMAP szerver.
• Több fiók is felvehető; a „Most ellenőriz” mindet szinkronizálja.
• Sok helyen alkalmazásjelszó kell (Gmail / Outlook / Yahoo / iCloud),
  nem a szokásos bejelentkezési jelszó.
• ProtonMail nincs támogatva (nincs sima IMAP).
• Most ellenőriz: új levelek behúzása.
• Teljes előzmény import: régebbi levelek is (lassabb).

Hírlevelek
• Bal oldalon válassz küldőt, vagy vedd fel: + Új hírlevél.
• Címke: csoportosítja a listát.
• Elrejtés: eltünteti a listából (nem törli); Elrejtettek… alatt visszaállítható.
• Törlés…: a hírlevelet és helyi leveleit végleg törli (a levelező fiókban megmaradnak).
• Helyi levelek törlése…: csak a levelek, a hírlevél a listában marad.
• Buborékon „Törlés”: egyetlen helyi levél.

Olvasás és keresés
• Középen a lista, jobbra a formázott levél.
• Szűrők: Összes / Olvasatlan / Kedvenc, vagy dátumtól.
• Keresés felül; Tallózáshoz válassz hírlevelet bal oldalon.

Mentés Word / PDF
• Egy levél: a buborékon vagy az olvasóban Word / PDF.
• Több levél: a lista fejlécén Word lista / PDF lista (a jelenlegi szűrés szerint).

Biztonsági mentés
• Fájl → Mentés biztonsági másolat…
• Beállítások → Mentési mappa (gépre)…
• Automata mentés: Beállításokban bekapcsolható (napi / heti / havi).
"""

MENTES_BIZTONSAG = """Mit tartalmaz a biztonsági mentés?
A mentés egy tömörített fájl (zip), benne az archívumod és a beállítások.
A beállításokban lehetnek a levelező fiók adatai (például alkalmazásjelszó).

Gépre mentés
A zip a választott mappába kerül. Ezt a mappát te őrzöd (lemez, USB, stb.).

Visszaállítás
Fájl → Visszaállítás backupból… — felülírja a jelenlegi archívumot.
Előtte a program biztonsági másolatot készít a régi állapotról.

Fontos
• A mentési fájlt kezelj bizalmasan (jelszó lehet benne).
• Ne oszd meg másokkal, és ne töltsd nyilvános helyre.
• Teljes kilépés előtt ellenőrizd, hogy a mentés sikeres volt-e.
"""

GOOGLE_DRIVE_BEJELENTKEZES = """Google Drive mentés

Egyszer (a programhoz):
• Beállítások → Google Drive előkészítés…
• A varázsló végigvezet, majd kiválasztod a Google-tól letöltött fájlt.

Utána minden felhasználó a saját Google-fiókjával:
1. Beállítások → Mentés helye → Google Drive
2. Beállítások → Google Drive bejelentkezés…
3. Böngészőben saját fiókkal engedélyezed
4. Fájl → Mentés biztonsági másolat… (vagy automata mentés)

A fájlok a saját Drive-odon a „HirlevelKoveto-backup” mappában lesznek.
"""

GOOGLE_DRIVE_NINCS_ELOKESZITVE = """A Google Drive még nincs előkészítve ennél a programnál.

Nyisd meg: Beállítások → Google Drive előkészítés…
Ott egy rövid lépéssor segít; utána mindenki a saját Google-fiókjával tud menteni.

Addig a gépre mentés elérhető:
Beállítások → Mentés helye → Gépre (mappa).
"""

ADATKEZELES = """Adatkezelés röviden

Helyi feldolgozás
• A levelek és beállítások az AppData mappádban tárolódnak (nem az interneten).
• A program a leveleződől (IMAP, SSL/TLS) olvassa a hírleveleket a megadott fiókokkal.
• Nincsen telemetria, nincsen központi szerver.

Adataid
• IMAP-jelszó (vagy alkalmazásjelszó): a config.json fájlban, NEM titkosítva
  → Javasolt: Gmail-nál alkalmazásjelszó, nem a teljes jelszó
  → Javasolt: Windows-jelszó + BitLocker (lemez-titkosítás) erősen ajánlott
• Levelek és metaadatok: SQLite adatbázis, helyi tárolás
• Jól ellenőrizd: ki fér hozzá az Ön gépéhez

Google Drive (opcionális)
• Ha bekapcsolod: a mentések az Ön Google-fiókon lesznek, Google biztonsagi szabályok szerint
• Teljes manuális kontroll: te döntöd el, hogy kívánsz-e menteni

Többet szeretnél?
Teljes GDPR-tájékoztatáshoz lásd a csomagban:
  ADATKEZELESI_TAJEKOZTATO.md
  BIZTONSAG_ES_ADATVEDELEM.md
"""

ADATVEDELEM_TELJES = """GDPR és Adatvédelem

Ez az alkalmazás 100%-ban helyi feldolgozást nyújt.
Minden adat az Ön gépén marad. Nincsen fejlesztői szerver, nincsen telemetria.

Adatkezelő: ÖN (saját gépén feldolgozás)
Feldolgozandó adatok: IMAP-jelszó, levelek, metaadatok, beállítások
Megőrzés: az Ön által irányítva (törlés, export, biztonsági mentés)
Az Ön jogai: hozzáférés, helyesbítés, törlés, adathordozhatóság
Panaszok: NAIH (Nemzeti Adatvédelmi és Információszabadság Hatóság)

Biztonsági kockázatok:
• Az IMAP-jelszó nincs titkosítva: física biztonsag az Ön feladata
• Ajánlott: alkalmazásjelszó + Windows-jelszó + BitLocker
• Adatbázis is helyi: Windows felhasználói jogosultságokra támaszkodva

Teljes tájékoztatás a csomagban:
  → ADATKEZELESI_TAJEKOZTATO.md (GDPR-kompatibilis)
  → BIZTONSAG_ES_ADATVEDELEM.md (biztonsági javaslatok)
  → FELHASZNALASI_FELTETELEK.md (EULA, licenc, felelősség)
  → LICENSE.md (MIT-licenc)
"""
