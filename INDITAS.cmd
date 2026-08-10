@echo off
cd /d "%~dp0"
title Hirlevel koveto

REM Hivatalos indito: eloszor az exe, ha nincs / Norton torte, Python

if exist "%~dp0program\HirlevelKoveto.exe" (
  start "" "%~dp0program\HirlevelKoveto.exe"
  exit /b 0
)

echo Nincs program\HirlevelKoveto.exe
echo 1^) Futtasd: BUILD-EXE.cmd
echo 2^) Vagy most Pythonnal indul...
echo.

set "PY="
set "PYW="
where pythonw >nul 2>&1 && set "PYW=pythonw"
where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
  set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
  set "PYW=%LocalAppData%\Programs\Python\Python313\pythonw.exe"
)
if not defined PY if exist "%LocalAppData%\Programs\Python\Python314\python.exe" (
  set "PY=%LocalAppData%\Programs\Python\Python314\python.exe"
  set "PYW=%LocalAppData%\Programs\Python\Python314\pythonw.exe"
)

if defined PYW if exist "%PYW%" (
  start "" "%PYW%" "%~dp0main.py"
  exit /b 0
)
if defined PY (
  start "" "%PY%" "%~dp0main.py"
  exit /b 0
)

echo Sem exe, sem Python. Futtasd: INSTALL.cmd majd BUILD-EXE.cmd
pause
exit /b 1
