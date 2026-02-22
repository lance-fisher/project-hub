@echo off
title ProjectsHome Startup
echo.
echo  ==========================================
echo   ProjectsHome Background Services
echo   Starting always-on services...
echo  ==========================================
echo.

:: 1. ProjectsHome Hub (port 8090)
echo [1/5] Starting ProjectsHome Hub...
netstat -ano | findstr :8090 | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
    echo       Already running on port 8090
) else (
    start "ProjectsHome Hub" /min cmd /c "cd /d D:\ProjectsHome\project-hub && python server.py"
    echo       Started on port 8090
)

:: 2. Git Sync (scheduled task - just verify)
echo [2/5] Verifying Git Sync task...
schtasks /Query /TN ProjectsHome-GitSync /FO LIST 2>nul | findstr "Ready Running" >nul
if %errorlevel%==0 (
    echo       Git Sync task is active
) else (
    echo       Git Sync task not found! Run setup-sync-task.ps1 to create it.
)

:: 3. Home Hub (port 3210)
echo [3/5] Starting Home Hub...
netstat -ano | findstr :3210 | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
    echo       Already running on port 3210
) else (
    if exist "D:\ProjectsHome\home-hub\server\dist\index.js" (
        start "Home Hub" /min cmd /c "cd /d D:\ProjectsHome\home-hub && node server\dist\index.js"
        echo       Started on port 3210
    ) else (
        echo       Server not built (run: cd home-hub ^&^& npm run build)
    )
)

:: 4. Auton (port 8095)
echo [4/5] Starting Auton (DRY_RUN mode)...
netstat -ano | findstr :8095 | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
    echo       Already running on port 8095
) else (
    start "Auton" /min cmd /c "cd /d D:\ProjectsHome\auton && python run.py"
    echo       Started on port 8095
)

:: 5. Run initial sync
echo [5/5] Running initial sync...
powershell -ExecutionPolicy Bypass -File "D:\ProjectsHome\project-hub\scripts\sync-all.ps1" >nul 2>&1
echo       Sync complete

echo.
echo  ==========================================
echo   All background services started.
echo   ProjectsHome Hub: http://localhost:8090
echo   Home Hub:         http://localhost:3210
echo   Auton:            http://localhost:8095
echo  ==========================================
echo.
echo You can close this window. Services will continue running.
timeout /t 5 /noq >nul
