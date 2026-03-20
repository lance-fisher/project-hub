' sync-all-silent.vbs - Truly silent wrapper for sync-all.ps1
' Prevents the console window flash that occurs when Task Scheduler
' runs powershell.exe directly with -WindowStyle Hidden.
'
' WScript.Shell.Run with window style 0 (SW_HIDE) prevents the
' console window from ever being created visually.

Dim scriptDir, psScript
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
psScript = scriptDir & "\sync-all.ps1"

CreateObject("WScript.Shell").Run _
    "powershell.exe -ExecutionPolicy Bypass -NonInteractive -File """ & psScript & """", _
    0, False
