@echo off
rem Doppelklick: entfernt das Programm. Die Daten bleiben erhalten, ausser Sie bestaetigen das Loeschen.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deinstallieren.ps1"
echo.
pause
