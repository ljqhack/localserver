@echo off
set serverpath=D:\localserver\
@echo ****************************************************
@echo ***********LOCALSERVER INSTALLER/UPDATER************
@echo ****************************************************
Rem 创建文件路径
set TempFile_Name=%SystemRoot%\System32\BatTestUACin_SysRt%Random%.batemp
::echo %TempFile_Name%
Rem 写入文件
( echo "BAT Test UAC in Temp" >%TempFile_Name% ) 1>nul 2>nul
Rem 判断写入是否成功
if exist %TempFile_Name% (
@echo START INSTALL...
@echo 请按照说明进行安装
pause
) else (
echo 请以管理员身份运行当前安装 
Rem 删除临时文件
del %TempFile_Name% 1>nul 2>nul
pause
exit
)

@echo *********请输入对应数字进行操作*********************
@echo ****1'安装服务器  2'更新服务器  3'重启服务器********
@echo ****************************************************
:CHOICE
set /p Number=数字:
if %Number%==1 goto INSTALL
if %Number%==2 goto UPDATE
if %Number%==3 goto RESTART
@echo 输入错误，请重新输入
goto CHOICE

:UPDATE
@echo 更新服务器程序...
@echo 1）查找并结束本地服务器进程
tasklist|findstr "localserver.exe"
if %errorlevel%==0 (
taskkill /F /IM localserver.exe)
pause
@echo 2）清除旧版本服务器程序
if exist %serverpath% (
for /f  %%i in ('dir /a-d /b %serverpath%\*.*') do (
del "%serverpath%\%%i" /f /q
)
rd %serverpath%\bat /S /q
)
pause
@echo 3）安装服务器程序
xcopy /e/c/h/z "%~pd0localserver\*.*" "%serverpath%"
md %serverpath%\data\db
schtasks /Run /TN localserver
@echo 更新成功
pause
exit

:RESTART
@echo 本地服务器重启中...
tasklist|findstr "localserver.exe"
if %errorlevel%==0 (
taskkill /F /IM localserver.exe)

tasklist|findstr "mongod.exe"
if %errorlevel%==0 (
taskkill /F /IM mongod.exe)

tasklist|findstr "mosquitto.exe"
if %errorlevel%==0 (
taskkill /F /IM mosquitto.exe)

schtasks /Run /TN localserver
@echo 重启成功
pause
exit


:INSTALL
if not exist C:\\"Program Files (x86)\"\mosquitto\ (
@echo 请以默认路径安装mosquitto，安装完成后按回车继续
start %~dp0\mosquitto-1.4.4-install-cygwin.exe
pause)
if not exist C:\\"Program Files (x86)\"\mosquitto\ (
@echo mosquitto未安装在默认路径，请重新安装
pause
exit
)
copy %~dp0\system\*.dll %SystemRoot%\System\

if not exist C:\OpenSSL-Win32\ (
@echo 请以默认路径安装Win32OpenSSL，安装完成后按回车继续
start %~dp0\Win32OpenSSL-1_0_2d.exe
pause)
if not exist C:\OpenSSL-Win32\ (
@echo Win32OpenSSL未安装在默认路径，请重新安装
pause
exit
)

if not exist C:\\"Program Files\"\MongoDB\Server\3.0\bin\ (
@echo 请以默认路径安装mongodb，安装完成后按回车继续
start %~dp0\mongodb-win32-x86_64-2008plus-ssl-3.0.6-signed.msi
pause)
if not exist C:\\"Program Files\"\MongoDB\Server\3.0\bin\ (
@echo mosquitto未安装在默认路径，请重新安装
pause
exit
)

pause

@echo 1）查找并结束本地服务器进程
tasklist|findstr "localserver.exe"
if %errorlevel%==0 (
taskkill /F /IM localserver.exe & @echo 结束进程成功) else (
@echo 服务器进程未在运行)
pause
@echo 2）清除旧版本服务器程序
if not exist %serverpath% (
@echo %serverpath%不存在) else (
rd %serverpath% /S /q)

@echo 3）安装服务器程序
xcopy /e/c/h/z "%~pd0localserver\*.*" "%serverpath%"
md %serverpath%\data\db

@echo 4）添加任务计划
@echo %~dp0
schtasks /Create /xml %~dp0\localserver.xml /tn localserver
::schtasks /Change /tn localserver /tr %serverpath%bat\base.vbs
schtasks /Run /TN localserver
@echo 安装成功！！
pause
