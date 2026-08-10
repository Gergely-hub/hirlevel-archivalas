"""Felhasználói súgó- és tájékoztató szövegek (nem fejlesztői)."""

from __future__ import annotations

APP_NAME = "Hírlevél követő"
APP_VERSION = "1.0"

NEVJEGY = f"""{APP_NAME}
Verzió: {APP_VERSION}

Hírlevelek helyi archívuma a leveleződből.
A levelek a gépeden maradnak; a program nem küldi el őket harmadik félnek,
kivéve ha te választod a Google Drive mentést.

Bezárás (X): a program a tálcán tovább fut.
Teljes kilépés: Fájl → Kilépés, vagy a tálca menü → Kilépés.
"""

SÚGÓ_ROVID = """Indítás
• Indítsd a Hírlevél követőt (INDITAS vagy a program ikonja).
• Ha „már fut” üzenetet kapsz: nézd a tálcát (óra mellett), ott megnyithatod.

Levelező fiók
• Levelezés → Levelező fiókok… — add meg a címedet és az alkalmazásjelszót
  (Gmailnél nem a szokásos jelszó, hanem az alkalmazásjelszó).
• Most ellenőriz: új levelek behúzása.
• Teljes előzmény import: régebbi levelek is (lassabb).

Hírlevelek
• Bal oldalon válassz küldőt, vagy vedd fel: + Új hírlevél.
• Címke: csoportosítja a listát.
• Elrejtés: eltünteti a listából (nem törli); Elrejtettek… alatt visszaállítható.

Olvasás és keresés
• Középen a lista, jobbra a formázott levél.
• Szűrők: Összes / Olvasatlan / Kedvenc, vagy dátumtól.
• Keresés felül; Tallózáshoz válassz hírlevelet bal oldalon.

Mentés Word / PDF
• Egy levél: a buborékon vagy az olvasóban Word / PDF.
• Több levél: a lista fejlécén Word lista / PDF lista (a jelenlegi szűrés szerint).

Biztonsági mentés
• Fájl → Mentés biztonsági másolat…
• Beállítások → Mentés helye: Gépre vagy Google Drive.
• Automata mentés: Beállításokban bekapcsolható (napi / heti / havi).
"""

MENTES_BIZTONSAG = """Mit tartalmaz a biztonsági mentés?
A mentés egy tömörített fájl (zip), benne az archívumod és a beállítások.
A beállításokban lehetnek a levelező fiók adatai (például alkalmazásjelszó).

Gépre mentés
A zip a választott mappába kerül. Ezt a mappát te őrzöd (lemez, USB, stb.).

Google Drive mentés
A program a saját Google-fiókodba tölti fel a mentést
(a „HirlevelKoveto-backup” mappába), böngészős engedély után.
Ehhez internet kell. A Drive asztali programja nem szükséges.

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

• A levelek és beállítások a saját Windows-felhasználói mappádban tárolódnak.
• A program a leveleződől (IMAP) olvassa a hírleveleket a megadott fiókkal.
• Harmadik félnek adatot csak akkor küld, ha te indítasz Google Drive mentést
  (akkor a mentési fájl a te Google-fiókodba kerül).
• Nincs reklám, nincs kötelező felhőfiók a mindennapi használathoz.
"""
