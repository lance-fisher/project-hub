@echo off
REM Quick manual sync - runs sync with verbose output
powershell -ExecutionPolicy Bypass -File "%~dp0sync-all.ps1" -Verbose
pause
