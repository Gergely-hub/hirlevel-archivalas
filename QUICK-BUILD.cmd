@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title HirlevelKoveto BUILD-ZIP
taskkill /IM HirlevelKoveto.exe /F >nul 2>&1
set BUILD_NOPAUSE=1
echo Build indul... (5-15 perc, Norton: lasd NORTON-BUILD.md)
call "%~dp0BUILD-ZIP.cmd"
