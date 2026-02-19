@echo off
title ProjectsHome Health Check
color 0B
echo.
echo  ==========================================
echo   ProjectsHome Health Check
echo   %date% %time%
echo  ==========================================
echo.

:: Check git sync task
echo  --- Services ---
schtasks /Query /TN ProjectsHome-GitSync /FO LIST 2>nul | findstr "Ready Running" >nul
if %errorlevel%==0 (
    echo   [OK] Git Sync Task           active
) else (
    echo   [--] Git Sync Task           NOT RUNNING
)

:: Check services by port
call :check_port 8090 "ProjectsHome Hub       "
call :check_port 8095 "Auton                  "
call :check_port 4000 "Master Trade Bot       "
call :check_port 4100 "Master Trading System  "
call :check_port 8080 "Polymarket Sniper      "
call :check_port 3210 "Home Hub               "
call :check_port 8070 "Lance Fisher Splash    "
call :check_port 8071 "Galleon Splash         "
call :check_port 8075 "Jump Quest             "
call :check_port 8076 "NoCo App Studio        "
call :check_port 8096 "one-three.net          "

echo.
echo  --- Git Repos ---
powershell -ExecutionPolicy Bypass -File "D:\ProjectsHome\project-hub\scripts\check-repos.ps1"

echo.
pause
goto :eof

:check_port
netstat -ano | findstr :%~1 | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
    echo   [OK] %~2 port %~1
) else (
    echo   [--] %~2 port %~1  ^(not running^)
)
goto :eof
