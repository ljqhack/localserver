Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "cmd /c E:\server\localserver.bat"
oShell.Run strArgs, 0, false