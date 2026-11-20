# Biztonsági és Adatvédelmi Nyilatkozat

**Hírlevél követő – Asztali Alkalmazás**

**Utolsó módosítás: 2026. október**

---

## 1. Bevezetés

Ez a dokumentum ismerteti az alkalmazás biztonsági jellemzőit, a feldolgozandó adatok védelmét, valamint az Ön által vállalt biztonsági felelősséget a **Hírlevél követő** asztali alkalmazás használata során.

**Fő biztonsági megállapítás:** Az Alkalmazás 100%-ban helyi feldolgozást nyújt. Az adatok nem kerülnek fejlesztői szerverekre, nincs központi szinkronizálás vagy telemetria. Az adatvédelem **az Ön operációs rendszer biztonságára és számítógép-fizikai biztonságára** támaszkodik.

---

## 2. Architektúra és Adatok Helye

### 2.1 Helyi Adatfeldolgozás
- **Feldolgozás:** Az Alkalmazás minden műveletet az Ön Windows-számítógépén végez
- **Tárolás:** Az összes adat az alábbi helyre kerül:
  ```
  %LOCALAPPDATA%\HirlevelKoveto\
  ├── config.json         (IMAP hitelesítés)
  ├── data\hirlevelek.db  (Hírlevelek és metaadatok)
  └── export\             (Exportált fájlok)
  ```
  Ez a mappa a Windows Fájlkezelőben így nyitható:
  ```
  C:\Users\[YourUsername]\AppData\Local\HirlevelKoveto\
  ```

### 2.2 Nincs szerverkommunikáció
- **Fejlesztői szerverek:** Az Alkalmazás **nem kommunikál** fejlesztői szerverekkel
- **Telemetria:** Nincs használati adatgyűjtés
- **Analitika:** Nincs nyomon követés vagy analytics
- **Frissítések:** Az Alkalmazás nem ellenőrzi automatikusan az új verziókat

### 2.3 IMAP-Kommunikáció Csak
Az Alkalmazás csak az Ön e-mail szolgáltatójához (pl. Gmail) csatlakozik:
- **IMAP protokoll** (SSL/TLS titkosítással)
- **Port:** 993 (Gmail és legtöbb szolgáltató)
- **Kommunikáció:** Az Alkalmazás az e-mailek letöltésére korlátozódik, nem küld adatokat vissza

---

## 3. Tárolt Adatok és Biztonsági Jellemzőik

### 3.1 `config.json` – IMAP Hitelesítés

**Tartalom:**
```json
{
  "imap_server": "imap.gmail.com",
  "email": "felhasznalo@gmail.com",
  "password": "xxxxxxxxxxxx",  // vagy alkalmazásjelszó
  "port": 993,
  "use_ssl": true
}
```

**Biztonsági státusz:**
- ❌ **TITKOSÍTÁS:** Nincs titkosítva
- ⚠️ **HOZZÁFÉRÉS:** Az Ön Windows felhasználójának jogosultságai korlátozzák az olvasást
- ⚠️ **FIZIKAI BIZTONSÁG:** Ha valaki hozzáféréshez jut az Ön számítógépéhez, szoftverrel kiolvasható

**Biztonsági Javaslatok:**
1. **Gmail-nál:** Használjon **alkalmazásjelszót** (App Password), nem a teljes Gmail-jelszót
   - Google Account → Security → App passwords
   - Ez a jelszó csak az Alkalmazáshoz használható, és külön inaktiválható
   - **Fontos:** az alkalmazásjelszó is titkosítás nélkül kerül a `config.json`-ba — jobb választás, de nem helyettesíti a BitLockert
2. **Más e-mail szolgáltató:** Ha elérhető, hasonló alkalmazásjelszó-mechanizmust használjon
3. **Gyenge jelszó:** Ne tároljunk egyszerű vagy gyenge jelszót itt

### 3.2 `hirlevelek.db` – SQLite Adatbázis

**Tartalom:**
- E-mail üzenetek szövege
- Feladó, tárgy, dátum
- Olvasott/olvasatlan státusz
- Hírlevel-forrás információk
- Felhasználó által hozzáadott megjegyzések

**Biztonsági státusz:**
- ❌ **TITKOSÍTÁS:** SQLite-adatbázis nem titkosított, nyílt szöveges
- ⚠️ **HOZZÁFÉRÉS:** Az Ön Windows felhasználójának jogosultságaira támaszkodva
- ⚠️ **KINYERÉS:** Ha valaki hozzáféréshez jut, az adatbázist máshol megnyithatja és olvashatja

**Miért nincs Titkosítás?**
- Az SQLite-ben a teljes titkosítás (pl. SQLCipher) külön telepítési lépéseket igényelne
- Ahelyett, az Alkalmazás az **operációs rendszer szintű** biztonságra támaszkodik
- Ez a tipikus gyakorlat asztali alkalmazásokra

### 3.3 Exportált Adatok

**Forráté:** `%LOCALAPPDATA%\HirlevelKoveto\export\`

Az Alkalmazás lehetővé teszi az adatbázis exportálását (pl. CSV, JSON):
- ❌ **TITKOSÍTÁS:** Az exportált fájlok nem titkosítottak
- ⚠️ **SZÁLLITÁS:** Ha e-mailben vagy szalagos meghajtón küldi el, a szállítás során biztonsági kockázat áll fenn

**Javaslat:** Exportált fájlokat szállítás előtt titkosítsa (pl. 7-Zip, BitLocker).

---

## 4. Szállítás Biztonság (Tranzit)

### 4.1 IMAP kommunikáció (Letöltés)
- **Titkosítás:** SSL/TLS (port 993)
- **Szerver igazolás:** Az Alkalmazás az IMAP-szerver tanúsítványát ellenőrzi
- **Biztonság:** ✅ Erős

## 5. Hozzáférés Vezérlés és Jogosultságok

### 5.1 Operációs Rendszer Szintű Védelmi
Az Alkalmazás adatai az alábbi helyeken tárolódnak:
```
C:\Users\[UserName]\AppData\Local\HirlevelKoveto\
```

**Hozzáférés:**
- Csak a **[UserName] Windows felhasználó** férhet hozzá alapértelmezés szerint
- Adminisztrátor (vagy akinek engedélyei vannak) szintén hozzáférhet
- Más felhasználók **nem látják** az adatokat

### 5.2 Többfelhasználós Rendszer
- Ha több Windows-felhasználó is használja ugyanazt a számítógépet:
  - Mindegyiknek saját `AppData\Local` mappája van
  - Az adatok **nem osztódnak meg** a felhasználók között
  - Minden felhasználó **saját Hírlevél követő konfigurációval** rendelkezik

---

## 6. Malware és Vírusvédelem

### 6.1 Alkalmazás Biztonság
- Az Alkalmazás **előre lefordított csomagként** érhető el (win64 zip); a forráskód nem közzétett
- Az **Ön ellenőrizheti** a teljes forráskódot – nincs rejtett kód
- Az EXE-fájl a forráskódból készül (PyInstaller)

### 6.2 Vírusfertőzés Kockázata
Az Alkalmazás maga **biztonsági kockázatot nem hordoz**, de:
- Ha a számítógép malware-vel megfertőződik:
  - Az adatbázis kiolvasható, az IMAP-jelszó kinyerhető
  - Az exportált fájlok ellophatók
  - Az e-mail fiók kompromittálódhat

### 6.3 Vírusvédelem Javaslat
1. **Antivírus szoftver** (pl. Windows Defender, Kaspersky, BitDefender) aktív használata
2. **Rendszeres Windows-frissítések**
3. **Biztonságos böngészési szokások** (nem kattintás gyanús linkekre)
4. **Letöltések ellenőrzése** (csak megbízható forrásból)

---

## 7. Fizikai Biztonság

### 7.1 Fizikai Hozzáférés Kockázata
Ha valaki **fizikai hozzáféréshez** jut az Ön számítógépéhez:
- ❌ Az adatbázis kiolvasható
- ❌ Az IMAP-jelszó kinyerhető (felhasználó bejelentkezés nélkül is)
- ❌ Az Alkalmazás konfigurációja módosítható

### 7.2 Lemez Titkosítás (Erősen Ajánlott)
**Windows 10/11 Pro/Enterprise:**
- **BitLocker** engedélyezése
- A teljes lemez titkosítása: `Ctrl+X` → Eszközök → BitLocker
- Jelszó vagy PIN szükséges az induláskor
- Biztonság: ✅ Nagyon erős

**Windows 10/11 Home:**
- Device Encryption (ha rendelkezésre áll)
- Vagy harmadik féltől származó titkosítás (pl. 7-Zip, VeraCrypt)

---

## 8. Adatvesztés és Helyreállítás

### 8.1 Biztonsági Másolat (Backup)
- Az Alkalmazás **nem készít automatikus biztonsági másolatot**
- Az Ön felelőssége, hogy:
  - Periodikusan biztonsági mentést készít (Fájl → Mentés… / Mentés másként…)
  - Vagy Windows Biztonsági mentésben szerepelteti a mappát

### 8.2 Adatvesztés Esete
Ha az `%LOCALAPPDATA%\HirlevelKoveto\` mappa törlésre kerül:
- ❌ Az adatok **nem helyreállíthatók** az Alkalmazásból
- ⚠️ Helyreállítás csak biztonsági másolatból lehetséges
- ⚠️ Az Alkalmazás fejlesztője **nem nyújt helyreállítási lehetőséget**

---

## 9. Harmadik Féltől Származó Adatok Biztonság

### 9.1 E-mailek Nyomon Követésé
Az Ön által letöltött e-mailek (hírlevelek) tartalmazhatnak:
- **Nyomkövetési pixelek** (1×1 képek, amelyek a megnyitást regisztrálják)
- **Externos linkok** (amelyek kattintásokat regisztrálnak)
- **Beágyazott script-ek** (amelyek adatokat gyűjthetnek)

**Az Alkalmazás nem nyújt védelmet ezek ellen.** A küldő (hírlevel-szolgáltató) láthatja, hogy:
- Megnyitotta az e-mailt (pixelpont tracking)
- Milyen linkekre kattintott (click tracking)

## 10. Alkalmazás Frissítések és Biztonsági Javítások

### 10.1 Frissítések Keresése
- Az Alkalmazás **nem ellenőrzi automatikusan** az új verziókat
- Az Ön felelőssége, hogy időnként ellenőrizze a GitHub-on: https://github.com/Gergely-hub/hirlevel-koveto/releases
- Biztonsági frissítések fontosak — ne hagyja figyelmen kívül

### 10.2 Frissítési biztonság
- Az Alkalmazás frissítéseit mindig a GitHub-ról töltse le (nem ismeretlen webhelyekről)
- Az EXE vagy telepítő **digitálisan aláírható** (jelenleg nem aláírt)
- Mielőtt telepítene, ellenőrizze a verziószámot és a kiadási megjegyzéseket

---

## 11. Biztonsági Ajánlások Lépésről Lépésre

### Első Telepítéskor
1. ✅ **GitHub-ról töltse le** az Alkalmazást (nem más forrásokból)
2. ✅ **Antivírus szoftverrel ellenőrizze** az EXE-fájlt
3. ✅ **Csomagolja ki** a GitHub Release **zip** csomagját, majd indítsa az **HirlevelKoveto.exe** fájlt (nincs aláírt Setup — szándékos)

### Az Alkalmazás Konfigurálása
4. ✅ **Gmail-nál:** Alkalmazásjelszót generáljon (nem a teljes jelszót)
5. ✅ **config.json:** Ne módosítsa manuálisan (az Alkalmazás felülete biztosít szerkesztést)

### Folyamatos biztonság
6. ✅ **Windows-frissítések:** Rendszeres telepítés
7. ✅ **Antivírus:** Naprakészen tartás és rendszeres vizsgálatok
8. ✅ **BitLocker:** Engedélyezés, ha Pro/Enterprise vagy Home Device Encryption
9. ✅ **Biztonsági mentés:** Hetente vagy havonta exportálja az adatokat
10. ✅ **Alkalmazás frissítések:** Havonta ellenőrizze a GitHub-on

### Az Alkalmazás Használata
11. ✅ **Erős Windows-jelszó:** Egyedi, legalább 12 karakteres jelszó
12. ✅ **Zárolt képernyő:** Munkahely elhagyásakor `Win+L`
13. ✅ **Fizikai biztonság:** Ne hagyja felügyelet nélkül a nyitott laptopot
14. ✅ **Bizalmas helyek:** Ne használja a köztelen Wi-Fi-ket az IMAP szinkronizáláshoz (lehetőleg otthonról)

---

## 12. Biztonsági incidensek és jelzések

### 12.1 Ha Gyanítja, hogy az IMAP Jelszó Kompromittálódott
1. **Azonnal** módosítsa az IMAP-jelszavát (vagy alkalmazásjelszót)
2. **Google Fiók (Gmail-nál):**
   - https://myaccount.google.com/security
   - Jelszó módosítása
   - App passwords: Az Alkalmazás jelszavát inaktiválja
3. **Az Alkalmazásban:** **Levelezés → Levelező fiókok…** → fiók törlése vagy új jelszó / új Microsoft bejelentkezés, majd Mentés

### 12.2 Ha Gyanítja, hogy az Adatbázis Sérült vagy Lopott
1. **Biztonsági másolatból** helyreállít (ha van)
2. **Eszközös lemezdiagnosztika** futtatása (Windows Lemezkezelés)
3. **Antivírus vizsgálat** a teljes rendszerre
4. **Figyelembe vétele:** Az e-mail szolgáltató naplóiban megnézheti, hogy ki fért hozzá a fiókjához

### 12.3 Biztonsági sebezhetőség jelzése
Ha biztonsági hibát talál:
1. **Súgó → Hibabejelentő…** — leírás a GitHub Issues oldalon (érzékeny adat nélkül)
2. Kritikus esetben kerülje a nyilvános részleteket; csak a reprodukálás lépéseit add meg

---

## 13. Biztonsági Szövegellenőrzés (Checklist)

| Ellenőrzendő | Státusz | Javaslat |
|---|---|---|
| Alkalmazás forrása | ✅ GitHub (nyílt) | Mindig GitHub-ról töltse le |
| IMAP jelszó titkosítása | ❌ Nincs | Használjon Google App Password-ot |
| Adatbázis titkosítása | ❌ Nincs | Engedélyezze a BitLocker-t |
| Fizikai hozzáférés védelem | ⚠️ OS-szint | Erős Windows-jelszó szükséges |
| Biztonsági másolat | ⚠️ Manuális | Fájl → Mentés… (zip a gépre) |
| Antivírus | ⚠️ Szoftver-függő | Windows Defender vagy más |
| Windows-frissítések | ⚠️ Szoftver-függő | Hetente legalább egyszer |
| Lemez titkosítás | ⚠️ Az Ön választása | Pro/Enterprise: BitLocker ajánlott |

---

## 14. Felelősség Nyilatkozat

Ez a biztonsági nyilatkozat **tájékoztató jellegű**. Az Alkalmazás fejlesztője:
- ❌ **Nem garantálja** az adatok biztonságát
- ❌ **Nem felelős** az Ön gépén tárolt adatok elvesztéséért vagy sérüléséért
- ❌ **Nem felelős** a jelszó-lopásért vagy az IMAP-fiók kompromittálódásáért
- ✅ **Javaslatokat nyújt** a jó gyakorlatokra (ld. fenti fejezetek)

Az Ön felelőssége az Alkalmazás és az adatai biztonsági gyakorlatának megvalósítása.

---

## 15. Kontakt és Támogatás

Biztonsági kérdéseihez vagy sérülékenységi jelzéseihez:
- **Hibabejelentő a programban:** Súgó → Hibabejelentő…
- **Web:** https://github.com/Gergely-hub/hirlevel-koveto/issues

---

**Készült: 2026. október | Hírlevél követő Alkalmazás**

*Ezt a nyilatkozatot rendszeresen frissíteni kell, ahogy az Alkalmazás fejlődik és az új biztonsági tapasztalatok szerzett javaslatok alapján.*
