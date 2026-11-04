@echo off
rem Doppelklick: installiert bzw. aktualisiert die Omikron Buchhaltung (ohne Administratorrechte)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installieren.ps1"
echo.
pause
