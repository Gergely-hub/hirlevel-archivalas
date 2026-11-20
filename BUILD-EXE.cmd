@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "PY="
REM Eloszor a 3.13 (biztos customtkinter) — ne a PATH-on levo 3.14
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python314\python.exe" set "PY=%LocalAppData%\Programs\Python\Python314\python.exe"
if not defined PY if exist "C:\Python314\python.exe" set "PY=C:\Python314\python.exe"
if not defined PY (
  echo Python kell a buildehez. Futtasd: INSTALL.cmd
  pause
  exit /b 1
)

echo [Build] HirlevelKoveto.exe  -^>  program\
REM Ha fut az app, az exe nem csereelheto — elozo build igy regi menut hagyott
taskkill /IM HirlevelKoveto.exe /F >nul 2>&1

REM Build idobelyeg (ellenorzes: program\HirlevelKoveto.exe --version)
"%PY%" "%~dp0scripts\write_build_info.py"
if errorlevel 1 ( echo build_info hiba & pause & exit /b 1 )

REM Kék boríték ikon (tálca = system tray)
"%PY%" "%~dp0scripts\make_app_icon.py"
if errorlevel 1 ( echo ikon hiba & pause & exit /b 1 )

if exist "_build_work" rmdir /s /q "_build_work"
if exist "_build_out" rmdir /s /q "_build_out"
"%PY%" -m pip install -q -r requirements.txt
if errorlevel 1 ( echo pip hiba & pause & exit /b 1 )
"%PY%" -m pip install -q pyinstaller
if errorlevel 1 ( echo pip hiba & pause & exit /b 1 )

REM Ideiglenes dist a projektben, majd atmasoljuk EGYSZERU program\ mappaba
"%PY%" -m PyInstaller --noconfirm --clean ^
  --name "HirlevelKoveto" ^
  --windowed ^
  --onedir ^
  --icon "%~dp0app\assets\hirlevel.ico" ^
  --distpath "_build_out" ^
  --workpath "_build_work" ^
  --specpath "_build_work" ^
  --paths "." ^
  --add-data "%~dp0config.example.json;." ^
  --add-data "%~dp0app\theme_assets;app/theme_assets" ^
  --add-data "%~dp0app\assets\hirlevel.ico;app/assets" ^
  --hidden-import=customtkinter ^
  --hidden-import=app.ctk_menu ^
  --hidden-import=app.themes ^
  --hidden-import=app.build_info ^
  --hidden-import=app.imap_providers ^
  --hidden-import=tkinterweb ^
  --hidden-import=htmldocx ^
  --hidden-import=app.export_rich ^
  --hidden-import=app.tray ^
  --hidden-import=app.app_icon ^
  --hidden-import=app.win_chrome ^
  --hidden-import=app.dpi ^
  --hidden-import=app.single_instance ^
  --hidden-import=app.help_text ^
  --hidden-import=app.about ^
  --hidden-import=app.usage_guide ^
  --hidden-import=app.legal_center ^
  --hidden-import=app.important_notice ^
  --hidden-import=app.accounts_ui ^
  --hidden-import=app.power_events ^
  --hidden-import=app.window_util ^
  --hidden-import=app.oauth2_outlook ^
  --hidden-import=msal ^
  --collect-submodules msal ^
  --hidden-import=app.sync_debug ^
  --hidden-import=pystray ^
  --hidden-import=PIL._tkinter_finder ^
  --collect-all customtkinter ^
  --collect-all darkdetect ^
  --collect-all tkinterweb ^
  --collect-all pystray ^
  main.py

if errorlevel 1 (
  echo Build sikertelen.
  pause
  exit /b 1
)

REM HTML dokumentumok előkészítése az _build_out-ban, hogy az xcopy másolja azokat is
mkdir "_build_out\HirlevelKoveto\Hivatalos" 2>nul
if exist "ADATKEZELESI_TAJEKOZTATO.html" copy /y "ADATKEZELESI_TAJEKOZTATO.html" "_build_out\HirlevelKoveto\Hivatalos\ADATKEZELESI_TAJEKOZTATO.html" >nul
if exist "FELHASZNALASI_FELTETELEK.html" copy /y "FELHASZNALASI_FELTETELEK.html" "_build_out\HirlevelKoveto\Hivatalos\FELHASZNALASI_FELTETELEK.html" >nul
if exist "BIZTONSAG_ES_ADATVEDELEM.html" copy /y "BIZTONSAG_ES_ADATVEDELEM.html" "_build_out\HirlevelKoveto\Hivatalos\BIZTONSAG_ES_ADATVEDELEM.html" >nul
if exist "LICENSE.html" copy /y "LICENSE.html" "_build_out\HirlevelKoveto\Hivatalos\LICENSE.html" >nul
if exist "ROLUNK.html" copy /y "ROLUNK.html" "_build_out\HirlevelKoveto\Hivatalos\ROLUNK.html" >nul
if exist "HASZNALATI_UTMUTATO.html" copy /y "HASZNALATI_UTMUTATO.html" "_build_out\HirlevelKoveto\Hivatalos\HASZNALATI_UTMUTATO.html" >nul
if exist "OLVASD.md" copy /y "OLVASD.md" "_build_out\HirlevelKoveto\OLVASD.md" >nul

if exist "program" rmdir /s /q "program"
if exist "program" (
  echo Nem tudom torolni a program\ mappat — zarj be minden HirlevelKoveto ablakot, majd ujra.
  pause
  exit /b 1
)
mkdir "program"
REM Az xcopy már másolja a Hivatalos mappát, mert az _build_out-ban van
xcopy /e /i /y "_build_out\HirlevelKoveto\*" "program\" >nul

rmdir /s /q "_build_out" 2>nul
rmdir /s /q "_build_work" 2>nul

echo.
echo Kesz. Exe: program\HirlevelKoveto.exe
"program\HirlevelKoveto.exe" --version 2>nul
echo.
echo Inditas elott: tálca ikon → Kilépés (ha fut), aztán az exe.
echo.
