Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "C:\bat\base.bat"
oShell.Run strArgs, 0, false