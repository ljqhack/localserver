import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json, time, sys, math, threading, schedule, socket
import logging, logging.handlers
import urllib.request, urllib.parse
from threading import Timer

LOGFILE = "E:\localserver.log"
logging.basicConfig(level=logging.DEBUG)
log = logging

#log = logging.getLogger('DEBUG')
#log.setLevel(logging.DEBUG)
#handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=10000000, backupCount=5)
#log.addHandler(handler)

log.debug('START DEBUG LOG')
ISOTIMEFORMAT='%Y-%m-%d %X'

MQREMOTEHOST = "121.40.198.143"
MQHOST = '127.0.0.1'
MQPORT = 1883

DBHOST = '127.0.0.1'
DBPORT = 27017

RemoteServer = 'http://test.brotherphp.com/xiangliang_web/api.php?m=index'
CMDSEND = '&a=sendstudesmove'
CMDCHECK = '&a=sendattendance'
ATTENDANCE = 'http://test.brotherphp.com/xiangliang_web/attendance/index.php'

SignRouterA = '00:0c:43:76:20:44'
SignRouterB = '00:0c:43:76:20:55'

THRESHOLD_TIME = 2

TimerDict = {}
TimerConstant = {}


def UdpServer():
    address = ('', 33333)  
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    s.bind(address)  
    while True:
        data, addr = s.recvfrom(2048)  
        if not data:  
            log.debug("client has exist")
            break
        if data.decode('utf-8') == 'Finding the server':
            s.sendto(b'LocalServer',addr)
    log.debug("UdpServer Close!!!!!")  
    s.close()

def EveryDayTask():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " +"do everyday task")
    f = urllib.request.urlopen(ATTENDANCE, timeout = 20)
    log.debug(f.read().decode('utf-8-sig'))
    clearDB = 1
def Task():
    schedule.every().day.at("00:10").do(EveryDayTask)
    while True:
        schedule.run_pending()
        time.sleep(1)
##########################################
#            Inside
#   *rssi0              
#    .                       .
# .............door..................
#    .                       .
#   *rssi1  
#
#            Outside
##########################################
#return value:
#0: out of school
#1: in school
#2: ignore status
A = 0
n = 0
def isInSchool(rssi0,rssi1):
    arg0 = 80
    dis0 = abs(rssi0)
    dis1 = abs(rssi1)
    if (dis0 < arg0) or (dis1 < arg0):
        if dis0 > dis1:
            log.debug("out of school %d %d",dis0,dis1)
            return 0
        elif dis0 < dis1:
            log.debug("in school %d %d",dis0, dis1)
            return 1
    else:
        log.debug("ignore status %d %d",dis0, dis1)
        return 2
'''
    distance0 = math.pow( 10,(abs(rssi0) - A) / (10*n) )
    distance1 = rssi1
    distance2 = rssi2
    distance3 = rssi3
    if distance0 > distance2 and distance1 > distance3:
        return 0
    elif distance2 > distance0 and distance3 > distance1:
        return 1
    else:
        return 2
'''

def SendToRemote(routertime, mac, state):
    log.debug("sent to remote %d %s %d", routertime, mac, state)
    params_dict = {"stimestamp":routertime, "mac":mac, "state":state}
    params = urllib.parse.urlencode(params_dict).encode('utf-8')
    f = urllib.request.urlopen(RemoteServer+CMDCHECK, params, timeout = 20)
    jstr=f.read().decode('utf-8-sig')
    print(jstr)
    TimerDict.pop(mac,None)
    
def CheckDo(routertime, mac, state):
    TIME_CONSTANT = 30
    if mac in TimerDict:
        if TimerDict[mac].isAlive():
            log.debug("alive mac in dict %s",mac)
            TimerDict[mac].cancel()
            TimerDict[mac] = Timer(TIME_CONSTANT, SendToRemote,[routertime, mac, state])
            TimerDict[mac].start()
        else:
            log.debug("ERROE IN CheckDo()")
    else:
        TimerDict[mac] = Timer(TIME_CONSTANT, SendToRemote,[routertime, mac, state])
        TimerDict[mac].start()



def LeaveCheckFunc(mac):
    dc = MongoClient(DBHOST, DBPORT)
    c = dc.xljy.sign_table.find_one({"mac":mac, "state":1})
    if int(time.time()) - c["time"] > 9:
        SendToRemote(int(time.time()), mac, 1)
    else:
        if TimerConstant[mac] != 0:
            TimerDict[mac] = Timer(10, LeaveCheckFunc,[mac])
            TimerDict[mac].start()
            TimerConstant[mac] = TimerConstant[mac] - 1
        else:
            TimerDict.pop(mac,None)
            TimerConstant.pop(mac,None)

def LeaveCheck(mac):
    if mac in TimerDict:
        ignore = 1
    else:
        TimerConstant[mac] = 10
        TimerDict[mac] = Timer(10, LeaveCheckFunc,[mac])
        TimerDict[mac].start()
    

def on_connect(client, userdata, rc):
    log.debug("Connected with result code "+str(rc))
    client.subscribe("UPLOAD/#")

VALIDRSSI = 95
THTIME = 50
def on_message(client, userdata, msg):
    data_str = msg.payload.decode('utf-8-sig')
    DBclient = MongoClient(DBHOST, DBPORT)
    try:
        log.debug(data_str)
        data_json = json.loads(data_str)
        log.debug('1')
        #log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " + "on_message:" + msg.topic+"  "+"Router:"+data_json["hostaddress"]+"  "+"Wristband:"+data_json["data"][0]["address"])
        if (data_json["hostaddress"] == SignRouterA) and (abs(data_json["rssi"]) < VALIDRSSI):
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "state":1, "time":int(time.time())})
                SendToRemote(data_json["routertime"], data_json["data"][0]["address"], 0)
            else:
                if (cursor["state"] == 0):
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"mac":1,"time":int(time.time())}})
                    SendToRemote(int(time.time()), data_json["data"][0]["address"], 0)
                elif (cursor["state"] == 1):
                    ignore = 1
        elif (data_json["hostaddress"] == SignRouterB) and (abs(data_json["rssi"]) < VALIDRSSI):
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"], "state":1})
            if cursor == None:
                ignore = 1
            else:
                LeaveCheck(data_json["data"][0]["address"])
        if data_json["type"] == "real_time":
            c = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"], "state":1})
            if c == None:
                ignore = 1
            else:
                DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"time":int(time.time())}})
            params_dict = {"stimestamp":data_json["data"][0]["time"], "mac":data_json["data"][0]["address"], "count":data_json["data"][0]["counts"]}
            params = urllib.parse.urlencode(params_dict).encode('utf-8')
            f = urllib.request.urlopen(RemoteServer+CMDSEND, params, timeout = 20)
            jstr=f.read().decode('utf-8-sig')
            if str(jstr) == '{"state":"success"}':
                log.debug("on_message:send data to remote server success")
            else:
                log.debug("on_message:send data to remote server failure")
        elif data_json["type"] == "history":
            DBclient.xljy.history.insert(data_json["data"][0])
            log.debug("on_message:insert a history data to database")
            params_dict = {"stimestamp":data_json["data"][0]["time"], "mac":data_json["data"][0]["address"], "count":data_json["data"][0]["counts"]}
            params = urllib.parse.urlencode(params_dict).encode('utf-8')
            f = urllib.request.urlopen(RemoteServer+CMDSEND, params, timeout = 20)
            jstr=f.read().decode('utf-8-sig')
            if str(jstr) == '{"state":"success"}':
                log.debug("on_message:send data to remote server success")
            else:
                log.debug("on_message:send data to remote server failure")
    except:
        log.debug("on_message:ERROR 001")
        log.debug(sys.exc_info())

if __name__ == "__main__":
    udp = threading.Thread(target = UdpServer)
    udp.setDaemon(True)
    udp.start()
    task = threading.Thread(target = Task)
    task.setDaemon(True)
    task.start()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQREMOTEHOST, MQPORT, 60)
    client.loop_forever()
