@echo off
@echo **********************************************************
@echo *****************���ط�������ʼ��װ***********************
@echo **********************************************************
@echo 1�����Ҳ��������ط���������
tasklist|findstr "mosquitto.exe"
if %errorlevel%==0 (
taskkill /F /IM mosquitto.exe & @echo �������̳ɹ�) else (
@echo ����������δ������)

@echo 2������ɰ汾����������
set serverpath=D:\localserver\
if not exist %serverpath% (
@echo %serverpath%������) else (
rd %serverpath% /S /q)

@echo 3����װ����������
xcopy /e/c/h/z "%~pd0*.*" "%serverpath%"
md %serverpath%\data\db


@echo 4���������ƻ�
@echo %~dp0
schtasks /Create /xml %~dp0\localserver.xml /tn localserver
schtasks /Change /tn localserver /tr %serverpath%bat\base.vbs
@echo ��װ�ɹ�����
pause
