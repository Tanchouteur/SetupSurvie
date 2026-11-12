@echo off
rem SetupSurvie managed updater
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update-windows.ps1" %*
set "SURVIE_EXIT=%ERRORLEVEL%"
if not "%SURVIE_NO_PAUSE%"=="1" pause
exit /b %SURVIE_EXIT%
