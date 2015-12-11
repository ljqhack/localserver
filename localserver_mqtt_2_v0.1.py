import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json, time, sys, math, threading, schedule, socket
import logging, logging.handlers
import urllib.request, urllib.parse
from threading import Timer

LOGFILE = "E:\localserver.log"
#logging.basicConfig(level=logging.DEBUG)
log = logging

log = logging.getLogger('DEBUG')
log.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=10000000, backupCount=5)
log.addHandler(handler)

log.debug('START DEBUG LOG')
ISOTIMEFORMAT='%Y-%m-%d %X'

MQREMOTEHOST = "121.40.198.143"
MQHOST = '127.0.0.1'
MQPORT = 1883

DBHOST = '127.0.0.1'
DBPORT = 27017

RemoteServer = 'http://xiangliang.airm2m.com/xiangliang_web/api.php?m=index'
CMDSEND = '&a=sendstudesmove'
CMDCHECK = '&a=sendattendance'
UPSTATUS = '&a=basestationstatus'
ATTENDANCE = 'http://xiangliang.airm2m.com/xiangliang_web/attendance/index.php'

#inside
SignRouterA = '00:0c:43:76:20:44'
#outside
SignRouterB = '00:0c:43:76:20:55'

THRESHOLD_TIME = 2

TimerDict = {}

def Initparam():
    global SignRouterA
    global SignRouterB
    global VALIDRSSI
    global RemoteServer
    global ATTENDANCE
    f = open("local.conf")
    lines = f.readlines()
    for line in lines:
        if line[0:11] == "SignRouterA":
            SignRouterA = line[12:29]
        elif line[0:11] == "SignRouterB":
            SignRouterB = line[12:29]
        elif line[0:9] == "validrssi":
            VALIDRSSI = int(line[10:])
        elif line[0:12] == "RemoteServer":
            RemoteServer = line[13:-1]
        elif line[0:10] == "ATTENDANCE":
            ATTENDANCE = line[11:-1]
def UdpServer():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime()) + "   " + "Start UDP Server")
    address = ('', 9527)  
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    s.bind(address)  
    while True:
        data, addr = s.recvfrom(2048)  
        if not data:  
            log.debug("client has exist")
            break
        if data.decode('utf-8') == 'Finding the server':
            s.sendto(b'LocalServer',addr)
            log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " + "UDP Request: %s %s",data.decode('utf-8'),addr)
    log.debug("UdpServer Close!!!!!")  
    s.close()

def EveryDayTask():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " +"do everyday task")
    f = urllib.request.urlopen(ATTENDANCE, timeout = 20)
    log.debug(f.read().decode('utf-8-sig'))
    clearDB = 1
def Task():
    log.debug("Init EveryDayTask")
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
    params_dict = {"stimestamp":int(time.time()), "mac":mac, "state":state}
    params = urllib.parse.urlencode(params_dict).encode('utf-8')
    f = urllib.request.urlopen(RemoteServer+CMDCHECK, params, timeout = 20)
    jstr=f.read().decode('utf-8-sig')
    log.debug(jstr)
    
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

def on_connect(client, userdata, rc):
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " + "Connected with result code "+str(rc))
    client.subscribe("UPLOAD/#")

VALIDRSSI = 100
THTIME = 50
def on_message(client, userdata, msg):
    data_str = msg.payload.decode('utf-8-sig')
    DBclient = MongoClient(DBHOST, DBPORT)
    try:
        log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +data_str)
        data_json = json.loads(data_str)
        #log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " + "on_message:" + msg.topic+"  "+"Router:"+data_json["hostaddress"]+"  "+"Wristband:"+data_json["data"][0]["address"])
        if (data_json["hostaddress"] == SignRouterA) and (abs(data_json["rssi"]) < VALIDRSSI):
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                log.debug('fist a')
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "first":SignRouterA, "time":int(time.time())})
            else:
                if (cursor["first"] == SignRouterB) and (int(time.time()) - cursor["time"] < THTIME):
                    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " + data_json["data"][0]["address"] + " enter the school!!")
                    SendToRemote(int(time.time()), data_json["data"][0]["address"], 0)
                    DBclient.xljy.sign_table.delete_many({"mac":data_json["data"][0]["address"]})
                elif (cursor["first"] == SignRouterA) or (int(time.time()) - cursor["time"] > THTIME):
                    log.debug('up a time')
                    res = DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"first":SignRouterA,"time":int(time.time())}})
                else:
                    log.debug('ig')
        elif (data_json["hostaddress"] == SignRouterB) and (abs(data_json["rssi"]) < VALIDRSSI):
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                log.debug('first b')
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "first":SignRouterB, "time":int(time.time())})
            else:
                if (cursor["first"] == SignRouterA) and (int(time.time()) - cursor["time"] < THTIME):
                    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " + data_json["data"][0]["address"] + " leave school!!")
                    client.publish("ALAMR",'{"time":'+str(int(time.time()))+',"mac":"'+data_json["data"][0]["address"]+'","action":"leave"}')
                    SendToRemote(int(time.time()), data_json["data"][0]["address"], 1)
                    DBclient.xljy.sign_table.delete_many({"mac":data_json["data"][0]["address"]})
                elif (cursor["first"] == SignRouterB) or (int(time.time()) - cursor["time"] > THTIME):
                    log.debug('ignore b time')
                    res = DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"first":SignRouterB,"time":int(time.time())}})
                else:
                    log.debug('ig')
        if data_json["type"] == "real_time":
            c = DBclient.xljy.realtime.find_one(data_json["data"][0])
            if c == None:
                DBclient.xljy.realtime.insert(data_json["data"][0])
                log.debug("on_message:insert a realtime data to database")
                params_dict = {"stimestamp":data_json["data"][0]["time"], "mac":data_json["data"][0]["address"], "count":data_json["data"][0]["counts"],"electricity":data_json["data"][0]["battery"]}
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
        elif data_json["type"] == "heartbeat":
            params_dict = {"ctime":data_json["routertime"], "mac":data_json["hostaddress"], "status":1}
            params = urllib.parse.urlencode(params_dict).encode('utf-8')
            f = urllib.request.urlopen(RemoteServer+UPSTATUS, params, timeout = 20)
            jstr=f.read().decode('utf-8-sig')
            log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"BaseStation Status Update,res:"+ str(jstr))
    except:
        log.debug("on_message:ERROR 001")
        log.debug(sys.exc_info())

def main():
    Initparam()
    f = urllib.request.urlopen(ATTENDANCE, timeout = 20)
    log.debug(f.read().decode('utf-8-sig'))
    udp = threading.Thread(target = UdpServer)
    udp.setDaemon(True)
    udp.start()
    task = threading.Thread(target = Task)
    task.setDaemon(True)
    task.start()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQHOST, MQPORT, 60)
    client.loop_forever()
main()
