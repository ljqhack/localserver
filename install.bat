@echo off
set serverpath=D:\localserver\
@echo ****************************************************
@echo ***********LOCALSERVER INSTALLER/UPDATER************
@echo ****************************************************
Rem �����ļ�·��
set TempFile_Name=%SystemRoot%\System32\BatTestUACin_SysRt%Random%.batemp
::echo %TempFile_Name%
Rem д���ļ�
( echo "BAT Test UAC in Temp" >%TempFile_Name% ) 1>nul 2>nul
Rem �ж�д���Ƿ�ɹ�
if exist %TempFile_Name% (
@echo START INSTALL...
@echo �밴��˵�����а�װ
pause
) else (
echo ���Թ���Ա������е�ǰ��װ 
Rem ɾ����ʱ�ļ�
del %TempFile_Name% 1>nul 2>nul
pause
exit
)

@echo *********�������Ӧ���ֽ��в���*********************
@echo ****1'��װ������  2'���·�����  3'����������********
@echo ****************************************************
:CHOICE
set /p Number=����:
if %Number%==1 goto INSTALL
if %Number%==2 goto UPDATE
if %Number%==3 goto RESTART
@echo �����������������
goto CHOICE

:UPDATE
@echo ���·���������...
@echo 1�����Ҳ��������ط���������
tasklist|findstr "localserver.exe"
if %errorlevel%==0 (
taskkill /F /IM localserver.exe)
pause
@echo 2������ɰ汾����������
if exist %serverpath% (
for /f  %%i in ('dir /a-d /b %serverpath%\*.*') do (
del "%serverpath%\%%i" /f /q
)
rd %serverpath%\bat /S /q
)
pause
@echo 3����װ����������
xcopy /e/c/h/z "%~pd0localserver\*.*" "%serverpath%"
md %serverpath%\data\db
schtasks /Run /TN localserver
@echo ���³ɹ�
pause
exit

:RESTART
@echo ���ط�����������...
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
@echo �����ɹ�
pause
exit


:INSTALL
if not exist C:\\"Program Files (x86)\"\mosquitto\ (
@echo ����Ĭ��·����װmosquitto����װ��ɺ󰴻س�����
start %~dp0\mosquitto-1.4.4-install-cygwin.exe
pause)
if not exist C:\\"Program Files (x86)\"\mosquitto\ (
@echo mosquittoδ��װ��Ĭ��·���������°�װ
pause
exit
)
copy %~dp0\system\*.dll %SystemRoot%\System\

if not exist C:\OpenSSL-Win32\ (
@echo ����Ĭ��·����װWin32OpenSSL����װ��ɺ󰴻س�����
start %~dp0\Win32OpenSSL-1_0_2d.exe
pause)
if not exist C:\OpenSSL-Win32\ (
@echo Win32OpenSSLδ��װ��Ĭ��·���������°�װ
pause
exit
)

if not exist C:\\"Program Files\"\MongoDB\Server\3.0\bin\ (
@echo ����Ĭ��·����װmongodb����װ��ɺ󰴻س�����
start %~dp0\mongodb-win32-x86_64-2008plus-ssl-3.0.6-signed.msi
pause)
if not exist C:\\"Program Files\"\MongoDB\Server\3.0\bin\ (
@echo mosquittoδ��װ��Ĭ��·���������°�װ
pause
exit
)

pause

@echo 1�����Ҳ��������ط���������
tasklist|findstr "localserver.exe"
if %errorlevel%==0 (
taskkill /F /IM localserver.exe & @echo �������̳ɹ�) else (
@echo ����������δ������)
pause
@echo 2������ɰ汾����������
if not exist %serverpath% (
@echo %serverpath%������) else (
rd %serverpath% /S /q)

@echo 3����װ����������
xcopy /e/c/h/z "%~pd0localserver\*.*" "%serverpath%"
md %serverpath%\data\db

@echo 4���������ƻ�
@echo %~dp0
schtasks /Create /xml %~dp0\localserver.xml /tn localserver
::schtasks /Change /tn localserver /tr %serverpath%bat\base.vbs
schtasks /Run /TN localserver
@echo ��װ�ɹ�����
pause
