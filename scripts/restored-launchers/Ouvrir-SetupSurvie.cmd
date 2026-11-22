@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0application\scripts\restaurer-donnees-windows.ps1" -Ouvrir
exit /b %ERRORLEVEL%
