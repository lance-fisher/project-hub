@echo off
title ProjectsHome Startup
echo.
echo  ==========================================
echo   ProjectsHome Background Services
echo   Starting always-on services...
echo  ==========================================
echo.

:: 1. ProjectsHome Hub (port 8090)
echo [1/3] Starting ProjectsHome Hub...
netstat -ano | findstr :8090 | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
    echo       Already running on port 8090
) else (
    start "ProjectsHome Hub" /min cmd /c "cd /d D:\ProjectsHome\project-hub && python server.py"
    echo       Started on port 8090
)

:: 2. Git Sync (scheduled task - just verify)
echo [2/3] Verifying Git Sync task...
schtasks /Query /TN ProjectsHome-GitSync /FO LIST 2>nul | findstr "Ready Running" >nul
if %errorlevel%==0 (
    echo       Git Sync task is active
) else (
    echo       Git Sync task not found! Run setup-sync-task.ps1 to create it.
)

:: 3. Run initial sync
echo [3/3] Running initial sync...
powershell -ExecutionPolicy Bypass -File "D:\ProjectsHome\project-hub\scripts\sync-all.ps1" >nul 2>&1
echo       Sync complete

echo.
echo  ==========================================
echo   All background services started.
echo   ProjectsHome Hub: http://localhost:8090
echo  ==========================================
echo.
echo You can close this window. Services will continue running.
timeout /t 5 /noq >nul
