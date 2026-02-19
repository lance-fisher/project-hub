@echo off
:: ProjectsHome Hub Launcher
:: Ensures the server is running, then opens the browser.
:: If server is already running, just opens the browser.
cd /d D:\ProjectsHome\project-hub
python server.py %1
pause
