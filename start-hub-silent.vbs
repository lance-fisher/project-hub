' ProjectsHome Hub - Silent Background Launcher
' Starts all background services (Ollama, OpenClaw, Hub, Home Hub, Auton, sync).
' Edge will restore the dashboard tab from previous session automatically.
' Safe to run multiple times - checks if already running.
Set WshShell = CreateObject("WScript.Shell")

' Start all background services (no console window)
WshShell.Run "pythonw ""D:\ProjectsHome\project-hub\start-background.pyw""", 0, False
