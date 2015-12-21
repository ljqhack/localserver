Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "cmd /c E:\server\mongo.bat"
oShell.Run strArgs, 0, false