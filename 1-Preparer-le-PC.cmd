@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\prepare-windows.ps1" %*
set "SURVIE_EXIT=%ERRORLEVEL%"
if not "%SURVIE_NO_PAUSE%"=="1" pause
exit /b %SURVIE_EXIT%
