@echo off
cd /d "%~dp0"
echo Hírlevél Követő - Outlook OAuth parancssoros teszt
echo.
echo 1) Nyit meg egy Microsoft bejelentkezest (device code).
echo 2) Ha sikerul, IMAP XOAUTH2-t is probal.
echo.
python scripts\test_outlook_oauth_cmd.py %*
echo.
pause
