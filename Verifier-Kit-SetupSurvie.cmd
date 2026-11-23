@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\dupliquer-kit-windows.ps1" -Verifier
exit /b %ERRORLEVEL%
