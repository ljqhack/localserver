Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "C:\bat\localserver.bat"
oShell.Run strArgs, 0, false