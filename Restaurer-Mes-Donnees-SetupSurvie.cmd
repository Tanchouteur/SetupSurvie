@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\restaurer-donnees-windows.ps1"
exit /b %ERRORLEVEL%
