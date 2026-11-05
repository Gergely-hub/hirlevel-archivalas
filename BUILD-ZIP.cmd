@echo off
cd /d "%~dp0"
setlocal

REM Friss program\ mappa (build szamlalo + PyInstaller)
call "%~dp0BUILD-EXE.cmd"
if errorlevel 1 (
  echo Zip keszites megszakadt — exe build hiba.
  pause
  exit /b 1
)

if not exist "%~dp0program\HirlevelKoveto.exe" (
  echo Hianyzik: program\HirlevelKoveto.exe
  pause
  exit /b 1
)

set "PY="
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY where python >nul 2>&1 && set "PY=python"

if not defined PY (
  echo Python kell a zip nevehez.
  pause
  exit /b 1
)

"%PY%" "%~dp0scripts\make_release_zip.py"
if errorlevel 1 (
  echo Zip keszites sikertelen.
  pause
  exit /b 1
)

echo.
echo Kesz: dist_release\ (HirlevelKoveto-{verzio}-win64.zip)
echo.
echo Terjesztes: GitHub Release — csak ezt a zip-et csatolod.
echo Letolto: csomag kicsomagolasa, majd HirlevelKoveto.exe inditasa.
echo Windows figyelmeztethez ismeretlen kiadora — Tovabbi informacio, Futtatas megis.
echo.
endlocal
