' ProjectsHome Hub + OpenClaw - Silent Background Launcher
' Starts hub server + OpenClaw gateway, then opens dashboard in Edge.
' Safe to run multiple times - checks if already running.
Set WshShell = CreateObject("WScript.Shell")

' Start hub server + OpenClaw gateway (no console window)
WshShell.Run "pythonw ""D:\ProjectsHome\project-hub\start-background.pyw""", 0, False

' Wait for server to start, then open dashboard
WScript.Sleep 4000
WshShell.Run "msedge --app=http://localhost:8090", 0, False
