@echo off
cd /d "%~dp0"
title Hirlevel koveto (Python)

REM Fejlesztoi inditas: mindig forraskod (pythonw), soha nem a program\ exe

set "PYW="
if exist "%LocalAppData%\Programs\Python\Python313\pythonw.exe" (
  set "PYW=%LocalAppData%\Programs\Python\Python313\pythonw.exe"
)
if not defined PYW if exist "%LocalAppData%\Programs\Python\Python314\pythonw.exe" (
  set "PYW=%LocalAppData%\Programs\Python\Python314\pythonw.exe"
)
if not defined PYW where pythonw >nul 2>&1 && set "PYW=pythonw"
if not defined PYW (
  echo pythonw nem talalhato. Futtasd: INSTALL.cmd
  pause
  exit /b 1
)

start "" "%PYW%" "%~dp0main.py"
exit /b 0
