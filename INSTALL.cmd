@echo off
cd /d "%~dp0"
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python314\python.exe" set "PY=%LocalAppData%\Programs\Python\Python314\python.exe"
if not defined PY if exist "C:\Python314\python.exe" set "PY=C:\Python314\python.exe"
if not defined PY (
  echo Python nincs a PATH-on. Telepitsd: https://www.python.org/downloads/
  echo Telepiteskor pipald be: "Add python.exe to PATH"
  pause
  exit /b 1
)
echo [Hirlevel koveto] Fuggosegek telepitese...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo HIBA: pip telepites sikertelen.
  pause
  exit /b 1
)
if not exist config.json (
  copy /y config.example.json config.json >nul
  echo.
  echo Letrejott a config.json — szerkeszd: levelezo fiok (IMAP) + jelszo.
)
echo.
echo Kesz. Kovetkezo: szerkeszd a config.json-t, majd START.cmd
pause
