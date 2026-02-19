@echo off
REM sync-all.bat - Wrapper for sync-all.ps1
REM Run from anywhere. Syncs all tracked repos with GitHub.
REM Usage: sync-all.bat [--verbose] [--push]

set SCRIPT_DIR=%~dp0
set PS_SCRIPT=%SCRIPT_DIR%sync-all.ps1

set ARGS=
if "%1"=="--verbose" set ARGS=-Verbose
if "%1"=="--push" set ARGS=-Push
if "%2"=="--verbose" set ARGS=%ARGS% -Verbose
if "%2"=="--push" set ARGS=%ARGS% -Push

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %ARGS%
