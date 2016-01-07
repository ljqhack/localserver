#coding=utf-8
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json, time,datetime, sys, math, threading, schedule, socket, os, traceback
import codecs
import logging, logging.handlers
import urllib.request, urllib.parse
from threading import Timer

Version = 1.00

LOGFILE = "E:\localserver.log"
#logging.basicConfig(level=logging.DEBUG)
log = logging

SCHOOLID = 1

ISOTIMEFORMAT='%Y-%m-%d %X'

MQREMOTEHOST = "121.40.198.143"
MQHOST = '127.0.0.1'
MQPORT = 1883

DBHOST = '127.0.0.1'
DBPORT = 27017

RemoteServer = 'http://xiangliang.airm2m.com/xiangliang_web/api.php?m=index'
CMDSEND = '&a=sendstudesmove'
CMDCHECK = '&a=sendattendance'
CMDGETNODE = '&a=getnode'
UPSTATUS = '&a=basestationstatus'
COMPLEMENT = '&a=complementstudesmove'
ATTENDANCE = 'http://xiangliang.airm2m.com/xiangliang_web/attendance/index.php'

#inside
SignRouterA = []
#outside
#SignRouterB = []

#VALIDRSSI_OUT = 100
VALIDRSSI_IN = 100

#TimerDict = {}
#TimerConstant = {}

#CHECK_NUMS = 10
#CHECK_TIMEOUT = 20
#TIME_THRESHOLD = 30

CalHistory = {}

CHECK_TIMEOUT = 60
TIME_THRESHOLD = 30

def getpwd():
    pwd = sys.path[0]
    if os.path.isfile(pwd):
        pwd = os.path.dirname(pwd)
    return pwd
def Initparam():
    global SignRouterA
    #global SignRouterB
    #global VALIDRSSI_OUT
    global VALIDRSSI_IN
    global RemoteServer
    global ATTENDANCE
    global log
    global LOGFILE
    global SCHOOLID
    #global TIME_THRESHOLD
    #global CHECK_NUMS
    #global CHECK_TIMEOUT
    f = codecs.open(getpwd()+"\local.conf","r","utf-8")
    lines = f.readlines()
    for line in lines:
        if line[0:11] == "SignRouterA":
            SignRouterA.append(line.split("=")[1].strip())
        elif line[0:12] == "VALIDRSSI_IN":
            VALIDRSSI_IN = int(line.split("=")[1].strip())
        elif line[0:12] == "RemoteServer":
            RemoteServer = line[13:-1].strip()
        elif line[0:10] == "ATTENDANCE":
            ATTENDANCE = line[11:-1].strip()
        elif line[0:7] == "LOGFILE":
            LOGFILE = line.split("=")[1].strip()
        elif line[0:8] == "schoolid":
            SCHOOLID = int( line.split("=")[1].strip() )
    log = logging.getLogger('DEBUG')
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=10000000, backupCount=5)
    log.addHandler(handler)
    log.debug('START DEBUG LOG')
    log.debug(SignRouterA)
    #log.debug(SignRouterB)
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime()) + "   " + "Init param Success")

def Initdb():
    #1'Get students list from remote server,and update mac_list in Mongodb
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime()) + "   " + "Init db")
    f = urllib.request.urlopen(RemoteServer+CMDGETNODE+"&schoolid="+str(SCHOOLID), timeout = 20)
    mac_list_str = f.read().decode('utf-8-sig')
    mac_list_json = json.loads(mac_list_str)
    DBclient = MongoClient(DBHOST, DBPORT)
    ret = DBclient.xljy.mac_list.find()
    if len(list(ret)) == 1:
        log.debug("Initdb: update mac list!")
        DBclient.xljy.mac_list.update_one({"Is":1},{"$set":{"mac_list":mac_list_json["data"]} })
    else:
        DBclient.xljy.mac_list.insert({"Is":1, "mac_list":mac_list_json["data"]})
    #2'Clear sign_table collection,delete old document 
    ret = DBclient.xljy.sign_table.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple()))} })
    if ret:
        log.debug("Initdb: Clear DB Collection,sign_table!")
    else:
        log.debug("Initdb: Clear DB sign_table,false!")
    #3'Clear realtime collection,delete old document 
    ret = DBclient.xljy.realtime.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple()))} })
    if ret:
        log.debug("Initdb: Clear DB Collection,realtime!")
    #4'Clear history collection,delete old document which time is 7 days ago
    ret = DBclient.xljy.history.delete_many({"start":{"$lte":int(time.mktime(datetime.date.today().timetuple())) - 24*60*60*7} })
    if ret:
        log.debug("Initdb: Clear DB Collection,history!")
    
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
            log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " + "UDP Request: %s %s",data.decode('utf-8'),addr)
    log.debug("UdpServer Close!!!!!")  
    s.close()

def EveryDayTask():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"do everyday task")
    #1'Attendance interface
    f = urllib.request.urlopen(ATTENDANCE, timeout = 20)
    log.debug(f.read().decode('utf-8-sig'))
    DBclient = MongoClient(DBHOST, DBPORT)
    #2'Handle history table
    CursorMax = DBclient.xljy.realtime.aggregate([{"$group":{"_id":"$mac","time_max":{"$max":"$time"}}}])
    CursorMax_list = list(CursorMax)
    if len(CursorMax_list) != 0:
        t_m = None
        for t_m in CursorMax_list:
            time_max_before = t_m["time_max"]
            #insert history
            history = DBclient.xljy.history.insert({"mac":t_m["_id"],"start":time_max_before + 60,"starttoend":[time_max_before + 60,int(time.mktime(datetime.date.today().timetuple())) - 60]})
    mac = None
    mac_list = list(DBclient.xljy.mac_list.find({"Is":1}))[0]["mac_list"]
    for mac in mac_list:
        if DBclient.xljy.sign_table.find({"mac":mac}).count() == 0:
            #insert history
            history = DBclient.xljy.history.insert({"mac":mac,"start":int(time.mktime(datetime.date.today().timetuple()))-86400,"starttoend":[int(time.mktime(datetime.date.today().timetuple()))-86400,int(time.mktime(datetime.date.today().timetuple())) - 60]})
    #3'Clear history/sign_table/realtime
    ret = DBclient.xljy.history.delete_many({"start":{"$lte":int(time.mktime(datetime.date.today().timetuple())) - 86400*7 } })
    if ret:
        log.debug("EveryDayTask: Clear DB Collection,history!")
    ret = DBclient.xljy.sign_table.drop()
    if ret:
        log.debug("EveryDayTask: Clear DB Collection,sign_table!")
    ret = DBclient.xljy.realtime.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple())) } })
    if ret:
        log.debug("EveryDayTask: Clear DB Collection,realtime!")
def CheckLeaveTask():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"CheckLeaveTask")
    dbc = MongoClient(DBHOST, DBPORT)
    sign = dbc.xljy.sign_table.find()
    sign_list = list(sign)
    cur = None
    for cur in sign_list:
        now = int(time.time())
        if now - cur["time"] > TIME_THRESHOLD:
            SendToRemote(now, cur["mac"], 1)
            dbc.xljy.sign_table.delete_one({"mac":cur["mac"]})
            log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +  "%s leave school",cur["mac"])
def Task():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"Init EveryDayTask")
    schedule.every().day.at("00:10").do(EveryDayTask)
    schedule.every(CHECK_TIMEOUT).seconds.do(CheckLeaveTask)
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
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"sent to remote %d %s %d", routertime, mac, state)
    params_dict = {"stimestamp":routertime, "mac":mac, "state":state}
    params = urllib.parse.urlencode(params_dict).encode('utf-8')
    f = urllib.request.urlopen(RemoteServer+CMDCHECK, params, timeout = 20)
    jstr=f.read().decode('utf-8-sig')
    log.debug(jstr)

def SendToRemoteCount(time, mac, count, electricity):
    params_dict = {"stimestamp":time, "mac":mac, "count":count,"electricity":electricity}
    params = urllib.parse.urlencode(params_dict).encode('utf-8')
    f = urllib.request.urlopen(RemoteServer+CMDSEND, params, timeout = 20)
    jstr=f.read().decode('utf-8-sig')
    if str(jstr) == '{"state":"success"}':
        log.debug("on_message:send data to remote server success")
        return True
    else:
        log.debug("on_message:send data to remote server failure")
        return False
'''    
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
'''

def LeaveCheckFunc(mac):
    dc = MongoClient(DBHOST, DBPORT)
    c = dc.xljy.sign_table.find_one({"mac":mac})
    if int(time.time()) - c["time"] > TIME_THRESHOLD:
        SendToRemote(int(time.time()), mac, 1)
        TimerDict.pop(mac,None)
        TimerConstant.pop(mac,None)
    else:
        if TimerConstant[mac] != 0:
            log.debug("LeaveCheckFunc: mac:%s times:%s", mac, 11 - TimerConstant[mac])
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
        TimerConstant[mac] = CHECK_NUMS
        TimerDict[mac] = Timer(CHECK_TIMEOUT, LeaveCheckFunc,[mac])
        TimerDict[mac].start()
        log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"leave check!")
    
def isInschoolMac(mac):
    for m in SignRouterA:
        if m.lower()==mac.lower():
            return True
    return False
def isOutschoolMac(mac):
    for m in SignRouterB:
        if m.lower()==mac.lower():
            return True
    return False

def gethistory_pack(watchaddress,history):
    param = {}
    param["type"] = "gethistory"
    param["watchaddress"] = watchaddress
    param["total"] = len(history)
    param["history"] = history
    json_param = json.dumps(param)
    return json_param
def historytoremote_pack(mac, start, end, data):
    if len(data) != ((end - start)/60 + 1):
        log.debug("history package is bad!!")
        return False
    param = []
    t = 0
    i = 0
    for t in range(start, end + 60, 60):
        param.append({"mac":mac, "count":data[i], "datetime":t})
        i = i + 1
    params_dict = {"data":param}
    params = urllib.parse.urlencode(params_dict).encode('utf-8')
    return params
    
    

def on_connect(client, userdata, rc):
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " + "Connected with result code "+str(rc))
    client.subscribe("UPLOAD/#")
    client.subscribe("updatestudesmove")

def on_message(client, userdata, msg):
    data_str = msg.payload.decode('utf-8-sig')
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +data_str)
    DBclient = MongoClient(DBHOST, DBPORT)
    if msg.topic == 'updatestudesmove':
        try:
            log.debug("Sync From Remote Server!")
            data_json = json.loads(data_str)
            mac = data_json["mac"]
            starttime = data_json["starttime"]
            endtime = data_json["endtime"]
            cur = DBclient.xljy.history.delete_many({"mac":mac, "start":{"$lte":endtime}})
            log.debug("Delete history table,mac:%s  total:%d", mac, cur.deleted_count)
        except:
            log.debug("on_message:ERROR 001")
            log.debug(sys.exc_info())
    else:
        try:
            data_json = json.loads(data_str)
            if (data_json["type"] == "real_time"):
                timestamp_today = int(time.mktime(datetime.date.today().timetuple()))
                hostaddress = data_json["hostaddress"]
                rssi = data_json["rssi"]
                mac = data_json["data"][0]["address"]
                time_wrist = data_json["data"][0]["time"]
                data_msg = data_json["data"][0]
                SignFlag = False
                if ( isInschoolMac( hostaddress ) ) and (abs(rssi) < VALIDRSSI_IN):
                    fil = {"mac":mac}
                    up = {"$set":{"time":int(time.time()), "state":1}}
                    cursor = DBclient.xljy.sign_table.find_one_and_update(fil, up, upsert = True)
                    SignFlag = True
                    if cursor == None:
                        SendToRemote(int(time.time()), mac, 0)
                        #insert history
                        CursorMin = DBclient.xljy.realtime.aggregate([{"$match":{"mac":mac, "time":{"$gte":timestamp_today} }},{"$group":{"_id":"$mac","time_min":{"$min":"$time"}}}])
                        CursorMin_list = list(CursorMin)
                        if len(CursorMin_list) != 0:
                            t_m = CursorMin_list[0]["time_min"] - 60
                        else:
                            t_m = time_wrist - 60
                        history = DBclient.xljy.history.insert({"mac":mac,"start":timestamp_today,"starttoend":[timestamp_today,t_m]})
                        #get history
                        datatobase = DBclient.xljy.history.find({"mac":mac,"start":{"$lte":time_wrist - 60, "$gte":time_wrist -604800}})
                        datatobase_list = list(datatobase)
                        dtob = []
                        for x in datatobase_list:
                            dtob.append(x["starttoend"])
                        json_data = gethistory_pack(mac, dtob)
                        log.debug("get history: %s", json_data)
                        client.publish("GETHISTORY", json_data)
                else:
                    fil = {"mac":mac, "state":1}
                    up = {"$set":{"time":int(time.time())}}
                    cursor = DBclient.xljy.sign_table.find_one_and_update(fil, up)
                    if cursor != None:
                        SignFlag = True      
                c = DBclient.xljy.realtime.find({"mac":mac,"time":{"$lte":time_wrist, "$gte":(time_wrist-240) }})
                c_list = list(c)
                c_count = c.count()
                if c_count == 0:
                    CursorMax = DBclient.xljy.realtime.aggregate([{"$match":{"mac":mac}},{"$group":{"_id":"$mac","time_max":{"$max":"$time"}}}])
                    CursorMax_list = list(CursorMax)
                    if len(CursorMax_list) != 0:
                        time_max_before = CursorMax_list[0]["time_max"]
                        if ( time_max_before != (time_wrist - 300) ):
                            #insert history
                            history = DBclient.xljy.history.insert({"mac":mac,"start":time_max_before + 60,"starttoend":[time_max_before + 60,time_wrist - 300]})
                if c_count == 5:
                    nothingtoupdate = 1
                else:
                    upload_flag = True
                    i = 5
                    t = 0
                    cc = None
                    for t in range(time_wrist-240,time_wrist+60,60):
                        for cc in c_list:
                            if cc["time"] == t:
                                upload_flag = False
                                break;
                            else:
                                upload_flag = True
                        if upload_flag:
                            if SendToRemoteCount(t, mac, data_msg["counts"+str(i)], data_msg["battery"]):
                                log.debug("insert realtime mac:%s  time=%d", mac, t)
                                DBclient.xljy.realtime.insert({"mac":mac, "time":t})
                        i = i - 1

            elif data_json["type"] == "history":
                mac = data_json["watchaddress"]
                start = data_json["start"]
                end = data_json["end"]
                data = data_json["data"]
                log.debug("Receive a history msg, mac:%s  start:%d  end:%d", mac, start, end)
                ret = DBclient.xljy.history.find_one_and_delete({"mac":mac, "start":start})
                if ret != None:
                    params = historytoremote_pack(mac, start, end, data)
                    if params:
                        f = urllib.request.urlopen(RemoteServer + COMPLEMENT, params, timeout = 20)
                        jstr=f.read().decode('utf-8-sig')
                        log.debug(jstr)
                        if str(jstr) == '{"state":"success"}':
                            log.debug("on_message:send history to remote server success")
                        else:
                            log.debug("on_message:send history to remote server failure!!!")
            elif data_json["type"] == "heartbeat":
                params_dict = {"ctime":data_json["routertime"], "mac":data_json["hostaddress"], "status":1, "schoolid":SCHOOLID}
                params = urllib.parse.urlencode(params_dict).encode('utf-8')
                f = urllib.request.urlopen(RemoteServer+UPSTATUS, params, timeout = 20)
                jstr=f.read().decode('utf-8-sig')
                log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"BaseStation Status Update,res:"+ str(jstr))
        except:
            log.debug("on_message:ERROR 002")
            log.debug(sys.exc_info())
def restart_program():
  python = sys.executable
  os.execl(python, python, * sys.argv)
def main():
    try:
        Initparam()
        time.sleep(5)
        Initdb()
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
    except:
        log.debug(sys.exc_info())
if __name__ == "__main__":        
    main()
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"Someting Unexpected happened,Server will restart in 120 seconds!!!!!!!!!!!!!!!Please check your network,or error has been raised!!!!!!!!!!!!!!!!!!")
    time.sleep(120)
    restart_program()
