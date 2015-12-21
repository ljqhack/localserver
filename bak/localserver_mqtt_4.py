import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json, time, sys, math
import logging, logging.handlers
import urllib.request, urllib.parse
from threading import Timer

LOGFILE = "E:\localserver.log"
logging.basicConfig(level=logging.DEBUG)
log = logging

#log = logging.getLogger('DEBUG')
#log.setLevel(logging.DEBUG)
#handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=100000, backupCount=5)
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

SignRouterA = '00:0c:43:76:20:22'
SignRouterB = 'AA:BB:CC:D2'
SignRouterC = '00:0c:43:76:20:77'
SignRouterD = 'AA:BB:CC:D4'

THRESHOLD_TIME = 2

TimerDict = {}

##########################################
#            Inside
#   *rssi0                *rss1
#    .                       .
# .............door..................
#    .                       .
#   *rssi2                *rssi3
#
#            Outside
##########################################
#return value:
#0: out of school
#1: in school
#2: ignore status
A = 0
n = 0
def isInSchool(rssi0,rssi1,rssi2,rssi3):
    arg0 = 72
    dis0 = abs(rssi0)
    dis1 = abs(rssi1)
    dis2 = abs(rssi2)
    dis3 = abs(rssi3)
    if (dis0 < arg0) or (dis1 < arg0) or (dis2 < arg0) or (dis3 < arg0):
        if (dis0 < dis2) and (dis1 < dis3):
            return 0
        elif (dis2 < dis0) and (dis3 < dis1):
            return 1
        else:
            return 2
    else:
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
            TimerDict[mac].cancel()
            TimerDict[mac] = Timer(TIME_CONSTANT, SendToRemote,[routertime, mac, state])
            TimerDict[mac].start()
        else:
            log.debug("ERROE IN CheckDo()")
    else:
        TimerDict[mac] = Timer(TIME_CONSTANT, SendToRemote,[routertime, mac, state])
        TimerDict[mac].start()

def on_connect(client, userdata, rc):
    log.debug("Connected with result code "+str(rc))
    client.subscribe("UPLOAD/#")
def on_message(client, userdata, msg):
    data_str = msg.payload.decode('utf-8-sig')
    DBclient = MongoClient(DBHOST, DBPORT)
    try:
        log.debug(data_str)
        data_json = json.loads(data_str)
        log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " + "on_message:" + msg.topic+"  "+"Router:"+data_json["hostaddress"]+"  "+"Wristband:"+data_json["data"][0]["address"])
        if data_json["hostaddress"] == SignRouterA:
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "rssi0":data_json["rssi"], "rssi1":0, "rssi2":0, "rssi3":0, "time":data_json["routertime"]})
            else:
                if data_json["routertime"] - cursor["time"] < THRESHOLD_TIME:
                    res = DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi0":data_json["rssi"]}})
                    if cursor["rssi1"] != 0 and cursor["rssi2"] != 0 and cursor["rssi3"] != 0:
                        ret = isInSchool(data_json["rssi"], cursor["rssi1"], cursor["rssi2"], cursor["rssi3"])
                        if ret == 0:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 1)
                        elif ret == 1:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 0)
                        elif ret == 2:
                            Ignore = 1
                        DBclient.xljy.sign_table.delete_many({"mac":data_json["data"][0]["address"]})
                        
                else:
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi0":data_json["rssi"], "rssi1":0, "rssi2":0, "rssi3":0, "time":data_json["routertime"]}})
        elif data_json["hostaddress"] == SignRouterB:
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "rssi0":0, "rssi1":data_json["rssi"], "rssi2":0, "rssi3":0, "time":data_json["routertime"]})
            else:
                if data_json["routertime"] - cursor["time"] < THRESHOLD_TIME:
                    res = DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi1":data_json["rssi"]}})
                    if cursor["rssi0"] != 0 and cursor["rssi2"] != 0 and cursor["rssi3"] != 0:
                        ret = isInSchool(cursor["rssi0"],data_json["rssi"], cursor["rssi2"], cursor["rssi3"])
                        if ret == 0:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 1)
                        elif ret == 1:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 0)
                        elif ret == 2:
                            Ignore = 1
                        DBclient.xljy.sign_table.delete_many({"mac":data_json["data"][0]["address"]})
                else:
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi0":data_json["rssi"], "rssi1":0, "rssi2":0, "rssi3":0, "time":data_json["routertime"]}})
        elif data_json["hostaddress"] == SignRouterC:
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "rssi0":0, "rssi1":0, "rssi2":data_json["rssi"], "rssi3":0, "time":data_json["routertime"]})
            else:
                if data_json["routertime"] - cursor["time"] < THRESHOLD_TIME:
                    res = DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi2":data_json["rssi"]}})
                    if cursor["rssi0"] != 0 and cursor["rssi1"] != 0 and cursor["rssi3"] != 0:
                        ret = isInSchool(cursor["rssi0"], cursor["rssi1"],data_json["rssi"], cursor["rssi3"])
                        if ret == 0:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 1)
                        elif ret == 1:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 0)
                        elif ret == 2:
                            Ignore = 1
                        DBclient.xljy.sign_table.delete_many({"mac":data_json["data"][0]["address"]})
                else:
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi0":data_json["rssi"], "rssi1":0, "rssi2":0, "rssi3":0, "time":data_json["routertime"]}})
        elif data_json["hostaddress"] == SignRouterD:
            cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
            if cursor == None:
                DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "rssi0":0, "rssi1":0, "rssi2":0, "rssi3":data_json["rssi"], "time":data_json["routertime"]})
            else:
                if data_json["routertime"] - cursor["time"] < THRESHOLD_TIME:
                    res = DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi3":data_json["rssi"]}})
                    if cursor["rssi0"] != 0 and cursor["rssi1"] != 0 and cursor["rssi2"] != 0:
                        ret = isInSchool(cursor["rssi0"], cursor["rssi1"], cursor["rssi2"],data_json["rssi"])
                        if ret == 0:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 1)
                        elif ret == 1:
                            CheckDo(data_json["routertime"], data_json["data"][0]["address"], 0)
                        elif ret == 2:
                            Ignore = 1
                        DBclient.xljy.sign_table.delete_many({"mac":data_json["data"][0]["address"]})
                else:
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"rssi0":data_json["rssi"], "rssi1":0, "rssi2":0, "rssi3":0, "time":data_json["routertime"]}})
                                  
        if data_json["type"] == "real_time":
            c = DBclient.xljy.realtime.find_one(data_json["data"][0])
            if c == None:
                DBclient.xljy.realtime.insert(data_json["data"][0])
                log.debug("on_message:insert a realtime data to database")
                #params_dict = {"stimestamp":data_json["data"][0]["time"], "mac":data_json["data"][0]["address"], "count":data_json["data"][0]["counts"]}
                #params = urllib.parse.urlencode(params_dict).encode('utf-8')
                #f = urllib.request.urlopen(RemoteServer+CMDSEND, params, timeout = 20)
                #jstr=f.read().decode('utf-8-sig')
                #if str(jstr) == '{"state":"success"}':
                #    log.debug("on_message:send data to remote server success")
                #else:
                #    log.debug("on_message:send data to remote server failure")
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
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQREMOTEHOST, MQPORT, 60)
    client.loop_forever()
