# Adatkezelési Tájékoztató

**Utolsó módosítás: 2026. október**

---

## 1. Bevezetés

A **Hírlevél követő** (a továbbiakban: „Alkalmazás") egy asztali számítógépes program, amely lehetővé teszi a felhasználók számára e-mail hírlevelek helyi archiválását és kezelését. Ez az adatkezelési tájékoztató ismerteti, hogyan kezeljük az Ön személyes adatait az Alkalmazás használata során.

**Alapelv:** Az Alkalmazás **100% lokálisan, az Ön számítógépén** működik. Nincsenek központi szerverek, nincs az Ön adatainak továbbítása harmadik félhez, és nincs telemetria vagy nyomon követés.

---

## 2. Adatkezelő és Jogalap

### 2.1 Adatkezelő
Az Alkalmazás használata során **Ön az adatkezelő**. Az Alkalmazás a saját gépén futva, az Ön irányítása alatt feldolgozza az adatokat. A fejlesztő nem működtet központi szervert, nem gyűjt adatokat, és nem tekinthető az Alkalmazás üzemeltetéséből adódó adatkezelőnek.

### 2.2 Jogalap
Az Alkalmazás működéséhez szükséges adatfeldolgozás az GDPR **6. cikk (1) bekezdés e) pontja** alapján történik: az Ön közérdekű feladat ellátása és a saját adatvédelmi kötelezettségei teljesítése.

---

## 3. Kezelt Személyes Adatok Köre

### 3.1 E-mail Fiók Hitelesítési Adatai
- **Mit tárolunk:** IMAP-kiszolgáló címe (pl. `imap.gmail.com`), e-mail cím, alkalmazásjelszó (vagy teljes jelszó, ha a felhasználó ezt választja)
- **Hol tárolódik:** `%LOCALAPPDATA%\HirlevelKoveto\config.json` (Windows felhasználói adatmappa — nem a program zip mappája)
- **Jellemzői:** Helyi fájlban, **nincs titkosítva** (FONTOS biztonsági nyilatkozat: ld. alább)
- **Kezelés célja:** IMAP-kiszolgálóhoz való kapcsolódás és e-mailek letöltése
- **Megőrzési időtartam:** Az Alkalmazás letöltéséig; az Ön által törölhető
- **Érintett jogok:** Hozzáférés, helyesbítés, törlés — **Levelezés → Levelező fiókok…** (fiók), főablak (levelek, források)

### 3.2 E-mail Üzenetek (Levelek) és Metaadatai
- **Mit tárolunk:** Levélszöveg, feladó, tárgy, dátum, melléklet hivatkozások, olvasott/olvasatlan státusz
- **Hol tárolódik:** Helyi SQLite adatbázis (`AppData\Local\HirlevelKoveto\data\hirlevelek.db`)
- **Jellemzői:** Helyi fájlban, az Ön számítógépén
- **Kezelés célja:** Hírlevelek archiválása, keresése és kategorizálása
- **Megőrzési időtartam:** Az Ön által definiálva (amíg az Alkalmazásban marad)
- **Érintett jogok:** Törlés (egyedi levél vagy teljes forrás), export

### 3.3 Hírlevel-Források (Félév Információ)
- **Mit tárolunk:** Hírlevél-forrás neve, feladó e-mail címe, címke, elrejtett/aktív állapot
- **Hol tárolódik:** Helyi SQLite adatbázis
- **Kezelés célja:** Források szervezése és kezelése
- **Megőrzési időtartam:** Az Ön által meghatározva
- **Érintett jogok:** Törlés (forrás és az összes kapcsolódó levél)

## 4. Adatszolgáltatás és Továbbítás

### 4.1 Harmadik Félnek Történő Továbbítás
Az Alkalmazás **nem továbbít személyes adatokat harmadik félhez**, kivéve:
- **IMAP-kiszolgálók:** Az Ön e-mail szolgáltatójához (pl. Gmail). Az Alkalmazás az IMAP protokollon keresztül kommunikál ezekkel a szerverekkel, de az e-mailek a saját gépén maradnak.

### 4.2 Fejlesztő Hozzáférése
A fejlesztő **nem fér hozzá** az Ön adataihoz. Az Alkalmazás nem kommunikál fejlesztői szerverekkel, nem küld telemetriát, és nem gyűjt információt az Ön használatáról.

---

## 5. Adatbiztonság

Az Alkalmazás helyi adatfeldolgozása előnyös az adatbiztonsági szempontból, de felelőssége van az Ön gépén:

### 5.1 Biztonsági Megoldások
- **Helyi tárolás:** Az összes adat az Ön számítógépén marad, nem továbbítódik.
- **Operációs rendszerbeli védelem:** Az Alkalmazás az Windows-fájlrendszer jogosultságait és az Ön felhasználói jelszavára támaszkodik.

### 5.2 Biztonsági Kockázatok (Felelősségre Vonás)
- **Jelszó-tárolás:** Az IMAP-jelszó (alkalmazásjelszó is) és az Outlook OAuth-tokenek az `config.json` fájlban **nincsenek titkosítva**. Ez azt jelenti, hogy ha valaki hozzáféréshez jut az Ön számítógépéhez, potenciálisan elérhetők a hitelesítési adatok.
  - **Alkalmazásjelszó:** Ahol a szolgáltató engedi (pl. Gmail), a teljes fiókjelszó helyett alkalmazásjelszó használata **biztonságosabb beállítás** (korlátozott, visszavonható) — a fájlban azonban így is olvasható formában marad.
  - **Megoldás:** Erős operációs rendszer jelszó, titkosított lemez (BitLocker, FileVault) használata.
- **Adatbázis:** Az SQLite-adatbázis is helyi, az operációs rendszer jogosultságaira támaszkodva védett.
- **Exportált fájlok:** Ha Ön exportálja az adatokat, az exportált fájlok ugyanilyen sérülékenyek.

### 5.3 Biztonsági Tanácsok
1. **Erős számítógépes jelszó** használata (Windows-bejelentkezés)
2. **Rendszeres operációs rendszer és szoftverfrissítések**
3. **Antivírus szoftver** aktív használata
4. **Lemez titkosítás** (BitLocker — Windows Pro/Enterprise)
5. **Alkalmazásjelszó használata Gmail-nél** (nem a teljes Gmail-jelszó)

---

## 6. Az Ön Jogai

Az Ön adatokhoz kapcsolódó jogai (GDPR VI. fejezet):

### 6.1 Hozzáférés Joga
Jogosult az Ön személyes adataihoz hozzáférni. Az Alkalmazásban megtekintheti a leveleket és forrásokat a főablakban; a fiókbeállításokat: **Levelezés → Levelező fiókok…**

### 6.2 Helyesbítés Joga
Jogosult pontatlan adatokat helyesbíteni: forrás szerkesztése (✎), **Címke**, fiók adatok mentése a Levelező fiókok ablakban.

### 6.3 Törlés Joga („Feledtetéshez Való Jog")
Jogosult személyes adatait törölni:
- **Egyedi levél:** törlés a levél buborékján
- **Forrás és levelek:** bal oldalon **Törlés…**
- **Csak helyi levelek:** **Helyi levelek törlése…**
- **Levelező fiók:** **Levelezés → Levelező fiókok… → Törlés**

### 6.4 Az Adatfeldolgozás Korlátozása
Jogosult adatfeldolgozást korlátozni: program bezárása/kilépés, forrás **Elrejtés**, ritkább **Beállítások → Frissítési intervallum**.

### 6.5 Adathordozhatóság
Jogosult adatait géppel olvasható, széles körben használt formátumban megkapni: **Word / PDF** export; teljes archívum: **Fájl → Mentés…** vagy **Mentés másként…** (zip).

### 6.6 Panasz Benyújtása
Jogosult panaszt benyújtani a felelős adatvédelmi hatóságnál (Magyarországon: [Nemzeti Adatvédelmi és Információszabadság Hatóság](https://www.naih.hu/)).

---

## 7. Gyermekek Adatai

Az Alkalmazás **nem célja a 16 év alattiak** osoby adatainak gyűjtése. Ha Ön szülő vagy gyám, és tudomásra jut, hogy gyermeke személyes adatait az Alkalmazás útján kezeltük, kérjük, vegye fel a kapcsolatot a fejlesztővel.

---

## 8. Adatmegőrzés

### 8.1 Alapelv
Az Alkalmazás által kezelt adatok **csak addig kerülnek megőrzésre, amíg szükségesek az Ön archiválási céljára**. Az Ön felelőssége azok törlése.

### 8.2 Továbbítási Adatok (Log-ok)
Az Alkalmazás **nem naplózza** IMAP-kommunikációt harmadik fél szerverére. A helyi naplók (ha vannak) az Ön lemezén maradnak.

---

## 9. Automatikus Döntéshozatal

Az Alkalmazás **nem használ** automatikus döntéshozatalt vagy profilozást az Ön adatainak feldolgozásában.

---

## 10. Harmadik Féltől Származó Tartalom

Az Alkalmazás által feldolgozott e-mailek (hírlevelek) harmadik felek (küldők) üzenetei. Az Alkalmazás nem felelős:
- A hírlevelek tartalmáért
- A küldő adatkezelési politikájáért
- Az e-mailek beágyazott nyomkövetési pixeljeiért vagy hivatkozásaiért

**Megjegyzés:** Az e-mailek megnyitásakor vagy a beágyazott képek betöltésekor a küldő szerveréhez való kapcsolódás az Ön böngészője/levelezőprogramja útján történik, és az alkalmazás nem kontrollálja.

---

## 11. Ezt a Tájékoztatót Érintő Módosítások

A fejlesztő jogosult ezt az adatkezelési tájékoztatót bármikor módosítani. Frissítés után az aktuális szöveg a programban elérhető: **Súgó → Jogi Dokumentumok Központ… → Adatkezelés**.

---

## 12. Kapcsolatfelvétel az Adatkezeléssel Kapcsolatos Kérdésekben

Ha kérdése van az adatkezelésről vagy szeretné gyakorolni fenti jogait, vegye fel a kapcsolatot:

- **Hibabejelentő / kérdés:** **Súgó → Hibabejelentő…** a programban ([GitHub Issues](https://github.com/Gergely-hub/hirlevel-koveto/issues))
- **Helyi Adatvédelmi Hatóság (Magyarország):** [Nemzeti Adatvédelmi és Információszabadság Hatóság (NAIH)](https://www.naih.hu/)

---

*Készült: 2026. október | Hírlevél követő alkalmazás*
