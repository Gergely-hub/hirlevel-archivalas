@echo off
cd /d "%~dp0"
setlocal

echo.
echo === Egyetlen build futas (PyInstaller 5-15 perc) ===
echo Ha Norton riaszt: engedelyezd a projekt mappat (lasd NORTON-BUILD.md).
echo Ne indits masik BUILD parancsot, amig ez fut.
echo.

taskkill /IM HirlevelKoveto.exe /F >nul 2>&1
if exist "build_egyfutas.log" del /f "build_egyfutas.log"

call "%~dp0BUILD-ZIP.cmd" >> "%~dp0build_egyfutas.log" 2>&1
set "RC=%errorlevel%"

echo.
echo === Kesz (exit %RC%) ===
echo Naplo: build_egyfutas.log
type "%~dp0build_egyfutas.log" | more +0
if exist "%~dp0program\HirlevelKoveto.exe" (
  "%~dp0program\HirlevelKoveto.exe" --version 2>nul
)
if exist "%~dp0dist_release\*.zip" (
  echo.
  dir /b "%~dp0dist_release\HirlevelKoveto-*-win64.zip" 2>nul
)
echo.
if not defined BUILD_NOPAUSE pause
endlocal
exit /b %RC%
