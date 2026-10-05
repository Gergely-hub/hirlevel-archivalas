# Biztonsági és Adatvédelmi Nyilatkozat

**Hírlevél követő – Asztali Alkalmazás**

**Utolsó módosítás: 2026. október**

---

## 1. Bevezetés

Ez a dokumentum ismerteti az alkalmazás biztonsági jellemzőit, a feldolgozandó adatok védelmét, valamint az Ön által vállalt biztonsági felelősséget a **Hírlevél követő** asztali alkalmazás használata során.

**Fő biztonsági megállapítás:** Az Alkalmazás 100%-ban helyi feldolgozást nyújt. Az adatok nem kerülnek fejlesztői szerverekre, nincsen központi szinkronizálás vagy telemetria. Az adatvédelem **az Ön operációs rendszer biztonságára és számítógép-fizikai biztonságára** támaszkodik.

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

### 2.2 Nincsen Szerver Kommunikáció
- **Fejlesztői szerverek:** Az Alkalmazás **nem kommunikál** fejlesztői szerverekkel
- **Telemetria:** Nincsen használati adatok gyűjtése
- **Analitika:** Nincsen nyomon követés vagy analytics
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
- ❌ **TITKOSÍTÁS:** Nincsen titkosítva
- ⚠️ **HOZZÁFÉRÉS:** Az Ön Windows felhasználójának jogosultságai korlátozzák az olvasást
- ⚠️ **FIZIKAI BIZTONSAG:** Ha valaki hozzáféréshez jut az Ön számítógépéhez, szoftver segítségével kiolvasható

**Biztonsági Javaslatok:**
1. **Gmail-nál:** Használjon **alkalmazásjelszót** (App Password), nem a teljes Gmail-jelszót
   - Google Account → Security → App passwords
   - Ez a jelszó csak az Alkalmazáshoz használható, és külön inaktiválható
2. **Más e-mail szolgáltató:** Ha disponible, hasonló alkalmazásjelszó-mechanizmust használjon
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

### 4.2 Google Drive Biztonsági Másolat (Opcionális)
Ha Ön engedélyezi a Google Drive biztonsági mentést:
- **Titkosítás:** OAuth 2.0 + HTTPS
- **Google-szerver:** Az Alkalmazás az Ön Google Drive-ján tárolt fájlokhoz a Google API-n keresztül fér hozzá
- **Biztonság:** ✅ Erős (Google biztonsági szintje)

---

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
- Az Alkalmazás **nyílt forráskódú** (GitHub-on elérhető)
- Az **Ön ellenőrizheti** a teljes forráskódot – nincsen rejtett kód
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
  - Google Drive biztonsági másolatot engedélyez (opcionális)
  - Vagy periodikusan manuálisan exportálja az adatokat
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

### 9.2 Google Drive OAuth Biztonsag
Ha engedélyezi a Google Drive biztonsági másolatot:
- Az Alkalmazás **csak az Ön beleegyezésével** kapja meg az hozzáférési jogosultságokat
- A Google megjeleníti az Ön **Hozzáférés engedélyezése** párbeszédében, hogy az Alkalmazás mely adatokhoz férhet hozzá
- **Mindig ellenőrizze** az engedélyek körét az OAuth képernyőn

---

## 10. Alkalmazás Frissítések és Biztonsági Javítások

### 10.1 Frissítések Keresése
- Az Alkalmazás **nem ellenőrzi automatikusan** az új verziókat
- Az Ön felelőssége, hogy időnként ellenőrizze a GitHub-on: https://github.com/[owner]/hirlevel-gmail-archivalas
- Biztonsági frissítések fontosak — ne hagyja figyelmen kívül

### 10.2 Frissítési Biztonsag
- Az Alkalmazás frissítéseit mindig a GitHub-ról töltse le (nem ismeretlen webhelyekről)
- Az EXE vagy telepítő **digitálisan aláírható** (jelenleg nem aláírt)
- Mielőtt telepítene, ellenőrizze a verziószámot és a kiadási megjegyzéseket

---

## 11. Biztonsági Ajánlások Lépésről Lépésre

### Első Telepítéskor
1. ✅ **GitHub-ról töltse le** az Alkalmazást (nem más forrásokból)
2. ✅ **Antivírus szoftverrel ellenőrizze** az EXE-fájlt
3. ✅ **Telepítse az Alkalmazást** (Inno Setup telepítő)

### Az Alkalmazás Konfigurálása
4. ✅ **Gmail-nál:** Alkalmazásjelszót generáljon (nem a teljes jelszót)
5. ✅ **config.json:** Ne módosítsa manuálisan (az Alkalmazás felülete biztosít szerkesztést)

### Folyamatos Biztonsag
6. ✅ **Windows-frissítések:** Rendszeres telepítés
7. ✅ **Antivírus:** Naprakészen tartás és rendszeres vizsgálatok
8. ✅ **BitLocker:** Engedélyezés, ha Pro/Enterprise vagy Home Device Encryption
9. ✅ **Biztonsági mentés:** Hetente vagy havonta exportálja az adatokat
10. ✅ **Alkalmazás frissítések:** Havonta ellenőrizze a GitHub-on

### Az Alkalmazás Használata
11. ✅ **Erős Windows-jelszó:** Egyedi, legalább 12 karakteres jelszó
12. ✅ **Zárolt képernyő:** Munkahely elhagyásakor `Win+L`
13. ✅ **Fizikai biztonsag:** Ne hagyja felügyelet nélkül a nyitott laptopot
14. ✅ **Bizalmas helyek:** Ne használja a köztelen Wi-Fi-ket az IMAP szinkronizáláshoz (lehetőleg otthonról)

---

## 12. Biztonsagi Incidensek és Jelzések

### 12.1 Ha Gyanítja, hogy az IMAP Jelszó Kompromittálódott
1. **Azonnal** módosítsa az IMAP-jelszavát (vagy alkalmazásjelszót)
2. **Google Fiók (Gmail-nál):**
   - https://myaccount.google.com/security
   - Jelszó módosítása
   - App passwords: Az Alkalmazás jelszavát inaktiválja
3. **Az Alkalmazásban:** Adatkezelés → IMAP hitelesítés törlése és új jelszó megadása

### 12.2 Ha Gyanítja, hogy az Adatbázis Sérült vagy Lopott
1. **Biztonsági másolatból** helyreállít (ha van)
2. **Eszközös lemezdiagnosztika** futtatása (Windows Lemezkezelés)
3. **Antivírus vizsgálat** a teljes rendszerre
4. **Figyelembe vétele:** Az e-mail szolgáltató naplóiban megnézheti, hogy ki fért hozzá a fiókjához

### 12.3 GitHub Issues-ben Biztonsagi Hibák Bejelentése
Ha biztonsági sebezhetőséget talál az Alkalmazásban:
1. **NE nyilvánosítsa** a GitHub-on (nyilvános issue)
2. **Írjon e-mailt** a fejlesztőnek (privát módon)
3. **Adja meg** a hiba leírását, a reprodukálási módot és a javasolt javítást

---

## 13. Biztonsági Szövegellenőrzés (Checklist)

| Ellenőrzendő | Státusz | Javaslat |
|---|---|---|
| Alkalmazás forrása | ✅ GitHub (nyílt) | Mindig GitHub-ról töltse le |
| IMAP jelszó titkosítása | ❌ Nincs | Használjon Google App Password-ot |
| Adatbázis titkosítása | ❌ Nincs | Engedélyezze a BitLocker-t |
| Fizikai hozzáférés védelem | ⚠️ OS-szint | Erős Windows-jelszó szükséges |
| Biztonsági másolat | ❌ Nincs (opcionális) | Google Drive vagy manuális export |
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

Biztonsagi kérdéseihez vagy sérülékenységi jelzéseihez:
- **GitHub Issues:** https://github.com/[owner]/hirlevel-gmail-archivalas/issues
- **Privát jelzés:** Az Issues lapon választható a biztonsag-bejelentés sablonja

---

**Készült: 2026. október | Hírlevél követő Alkalmazás**

*Ezt a nyilatkozatot rendszeresen frissíteni kell, ahogy az Alkalmazás fejlődik és az új biztonsági tapasztalatok szerzett javaslatok alapján.*
