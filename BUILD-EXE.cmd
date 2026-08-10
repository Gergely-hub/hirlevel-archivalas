@echo off
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
"%PY%" -m pip install -q -r requirements.txt
if errorlevel 1 ( echo pip hiba & pause & exit /b 1 )
"%PY%" -m pip install -q pyinstaller
if errorlevel 1 ( echo pip hiba & pause & exit /b 1 )

REM Ideiglenes dist a projektben, majd atmasoljuk EGYSZERU program\ mappaba
"%PY%" -m PyInstaller --noconfirm --clean ^
  --name "HirlevelKoveto" ^
  --windowed ^
  --onedir ^
  --distpath "_build_out" ^
  --workpath "_build_work" ^
  --specpath "_build_work" ^
  --paths "." ^
  --add-data "%~dp0config.example.json;." ^
  --hidden-import=customtkinter ^
  --hidden-import=app.ctk_menu ^
  --hidden-import=app.imap_providers ^
  --hidden-import=tkinterweb ^
  --hidden-import=htmldocx ^
  --hidden-import=app.export_rich ^
  --hidden-import=app.tray ^
  --hidden-import=app.gdrive_backup ^
  --hidden-import=app.single_instance ^
  --hidden-import=app.help_text ^
  --hidden-import=pystray ^
  --hidden-import=googleapiclient ^
  --hidden-import=google_auth_oauthlib ^
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

if exist "program" rmdir /s /q "program"
if exist "program" (
  echo Nem tudom torolni a program\ mappat — zarj be minden HirlevelKoveto ablakot, majd ujra.
  pause
  exit /b 1
)
mkdir "program"
xcopy /e /i /y "_build_out\HirlevelKoveto\*" "program\" >nul
if exist "OLVASD.md" copy /y "OLVASD.md" "program\OLVASD.md" >nul

rmdir /s /q "_build_out" 2>nul
rmdir /s /q "_build_work" 2>nul

echo.
echo Kesz. Inditas: INDITAS.cmd
echo Exe: program\HirlevelKoveto.exe
echo.
