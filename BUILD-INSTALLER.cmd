@echo off
cd /d "%~dp0"
setlocal

REM 1) Friss program\ mappa (PyInstaller)
call "%~dp0BUILD-EXE.cmd"
if errorlevel 1 (
  echo Az exe build sikertelen — telepítő nem készül.
  pause
  exit /b 1
)

if not exist "%~dp0program\HirlevelKoveto.exe" (
  echo Hianyzik: program\HirlevelKoveto.exe
  pause
  exit /b 1
)

REM 2) Inno Setup fordító megkeresése
set "ISCC="
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC where ISCC >nul 2>&1 && set "ISCC=ISCC"

if not defined ISCC (
  echo Inno Setup 6 kell a telepítőhöz.
  echo Telepítés: winget install JRSoftware.InnoSetup
  pause
  exit /b 1
)

echo.
echo [Installer] Inno Setup: "%ISCC%"
if exist "%~dp0dist_installer" rmdir /s /q "%~dp0dist_installer"
mkdir "%~dp0dist_installer" 2>nul

"%ISCC%" "%~dp0installer\HirlevelKoveto.iss"
if errorlevel 1 (
  echo Telepítő build sikertelen.
  pause
  exit /b 1
)

echo.
echo Kesz telepítő:
dir /b "%~dp0dist_installer\*.exe"
echo.
echo Fajl: %~dp0dist_installer\HirlevelKoveto-Setup.exe
echo.
endlocal
