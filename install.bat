@echo off
@echo **********************************************************
@echo *****************本地服务器开始安装***********************
@echo **********************************************************
@echo 1）查找并结束本地服务器进程
tasklist|findstr "mosquitto.exe"
if %errorlevel%==0 (
taskkill /F /IM mosquitto.exe & @echo 结束进程成功) else (
@echo 服务器进程未在运行)

@echo 2）清除旧版本服务器程序
set serverpath=D:\localserver\
if not exist %serverpath% (
@echo %serverpath%不存在) else (
rd %serverpath% /S /q)

@echo 3）安装服务器程序
xcopy /e/c/h/z "%~pd0*.*" "%serverpath%"
md %serverpath%\data\db


@echo 4）添加任务计划
@echo %~dp0
schtasks /Create /xml %~dp0\localserver.xml /tn localserver
schtasks /Change /tn localserver /tr %serverpath%bat\base.vbs
@echo 安装成功！！
pause
