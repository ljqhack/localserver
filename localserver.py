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
ATTENDANCE = 'http://xiangliang.airm2m.com/xiangliang_web/attendance/index.php'

#inside
SignRouterA = []
#outside
SignRouterB = []

VALIDRSSI_OUT = 100
VALIDRSSI_IN = 100

TimerDict = {}
TimerConstant = {}

CHECK_NUMS = 10
CHECK_TIMEOUT = 20
TIME_THRESHOLD = 30

CalHistory = {}

def getpwd():
    pwd = sys.path[0]
    if os.path.isfile(pwd):
        pwd = os.path.dirname(pwd)
    return pwd
def Initparam():
    global SignRouterA
    global SignRouterB
    global VALIDRSSI_OUT
    global VALIDRSSI_IN
    global RemoteServer
    global ATTENDANCE
    global log
    global LOGFILE
    global SCHOOLID
    global TIME_THRESHOLD
    global CHECK_NUMS
    global CHECK_TIMEOUT
    f = codecs.open(getpwd()+"\local.conf","r","utf-8")
    lines = f.readlines()
    for line in lines:
        if line[0:11] == "SignRouterA":
            SignRouterA.append(line.split("=")[1].strip())
        elif line[0:11] == "SignRouterB":
            SignRouterB.append(line.split("=")[1].strip())
        elif line[0:13] == "VALIDRSSI_OUT":
            VALIDRSSI_OUT = int(line.split("=")[1].strip())
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
        elif line[0:14] == "TIME_THRESHOLD":
            TIME_THRESHOLD = int( line.split("=")[1].strip() )
        elif line[0:11] == "CHECK_NUMS":
            CHECK_NUMS = int( line.split("=")[1].strip() )
        elif line[0:14] == "CHECK_TIMEOUT":
            CHECK_TIMEOUT = int( line.split("=").strip() )
    log = logging.getLogger('DEBUG')
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=10000000, backupCount=5)
    log.addHandler(handler)
    log.debug('START DEBUG LOG')
    log.debug(SignRouterA)
    log.debug(SignRouterB)
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime()) + "   " + "Init param Success")

def Initdb():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime()) + "   " + "Init db")
    f = urllib.request.urlopen(RemoteServer+CMDGETNODE+"&schoolid="+str(SCHOOLID), timeout = 20)
    mac_list_str = f.read().decode('utf-8-sig')
    mac_list_json = json.loads(mac_list_str)
    print(mac_list_json)
    DBclient = MongoClient(DBHOST, DBPORT)
    ret = DBclient.xljy.mac_list.find()
    if len(list(ret)) == 1:
        log.debug("Initdb: update mac list!")
        DBclient.xljy.mac_list.update_one({"Is":1},{"$set":{"mac_list":mac_list_json["data"]} })
    else:
        DBclient.xljy.mac_list.insert({"Is":1, "mac_list":mac_list_json["data"]})
    #xx = DBclient.xljy.mac_list.find({"Is":1})
    #print(list(xx)[0]["mac_list"])
    ret = DBclient.xljy.sign_table.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple()))} })
    if ret:
        log.debug("Initdb: Clear DB Collection,sign_table!")
    else:
        log.debug("Initdb: Clear DB sign_table,false!")
    ret = DBclient.xljy.realtime.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple()))} })
    if ret:
        log.debug("Initdb: Clear DB Collection,realtime!")
    
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
    f = urllib.request.urlopen(ATTENDANCE, timeout = 20)
    log.debug(f.read().decode('utf-8-sig'))
    DBclient = MongoClient(DBHOST, DBPORT)
    ######handle history table#######
    CursorMax = DBclient.xljy.realtime.aggregate([{"$group":{"_id":"$mac","time_max":{"$max":"$time"}}}])
    CursorMax_list = list(CursorMax)
    if len(CursorMax_list) != 0:
        t_m = None
        for t_m in CursorMax_list:
            time_max_before = t_m["time_max"]
            #insert history
            history = DBclient.xljy.history.insert({"mac":t_m["mac"],"start":time_max_before + 60,"end":int(time.mktime(datetime.date.today().timetuple())) - 60})
    mac = None
    mac_list = list(DBclient.xljy.mac_list.find({"Is":1}))[0]["mac_list"]
    for mac in mac_list:
        if DBclient.xljy.sign_table.find({"mac":mac}).count() == 0:
            #insert history
            history = DBclient.xljy.history.insert({"mac":mac,"start":int(time.mktime(datetime.date.today().timetuple()))-86400,"end":int(time.mktime(datetime.date.today().timetuple())) - 60})
    ret = DBclient.xljy.history.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple())) - 86400*7 } })
    if ret:
        log.debug("EveryDayTask: Clear DB Collection,history!")
    ret = DBclient.xljy.sign_table.drop()
    if ret:
        log.debug("EveryDayTask: Clear DB Collection,sign_table!")
    ret = DBclient.xljy.realtime.delete_many({"time":{"$lte":int(time.mktime(datetime.date.today().timetuple())) - 86400 } })
    if ret:
        log.debug("EveryDayTask: Clear DB Collection,realtime!")
def Task():
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"Init EveryDayTask")
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
    log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"   " +"sent to remote %d %s %d", routertime, mac, state)
    params_dict = {"stimestamp":int(time.time()), "mac":mac, "state":state}
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
            cur = DBclient.xljy.history.delete_many({"mac":mac, "start":{"$gte":starttime,"$lte":endtime}, "end":{"$gte":starttime,"$lte":endtime}})
            log.debug("Delete history table,mac:%s  total:%d", mac, cur.deleted_count)
        except:
            log.debug("on_message:ERROR 001")
            log.debug(sys.exc_info())
    else:
        try:
            data_json = json.loads(data_str)
            #log.debug(time.strftime( ISOTIMEFORMAT, time.localtime())+"  " + "on_message:" + msg.topic+"  "+"Router:"+data_json["hostaddress"]+"  "+"Wristband:"+data_json["data"][0]["address"])
            if ( isInschoolMac(data_json["hostaddress"]) ) and (abs(data_json["rssi"]) < VALIDRSSI_IN):
                cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
                if cursor == None:
                    DBclient.xljy.sign_table.insert({"mac":data_json["data"][0]["address"], "state":1, "time":int(time.time())})
                    SendToRemote(data_json["routertime"], data_json["data"][0]["address"], 0)
                    #insert history
                    history = DBclient.xljy.history.insert({"mac":data_json["data"][0]["address"],"start":int( time.mktime(datetime.date.today().timetuple()) ),"end":data_json["data"][0]["time"] - 60})
            elif (isOutschoolMac(data_json["hostaddress"])) and (abs(data_json["rssi"]) < VALIDRSSI_OUT):
                cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"], "state":1})
                if cursor == None:
                    log.debug("come from outschool basestation, Ignore,no sign!  %s", data_json["data"][0]["address"])
                else:
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"time":int(time.time())}})
                    LeaveCheck(data_json["data"][0]["address"])
                    log.debug("come from outschool basestation, will check leave!  %s", data_json["data"][0]["address"])
            if (data_json["type"] == "real_time") and ( not isOutschoolMac(data_json["hostaddress"]) ):
                ###update sign_table time
                cursor = DBclient.xljy.sign_table.find_one({"mac":data_json["data"][0]["address"]})
                if cursor != None:
                    log.debug("come from inschool/normal basestation, update mac time!  %s", data_json["data"][0]["address"])
                    DBclient.xljy.sign_table.update_one({"mac":data_json["data"][0]["address"]}, {"$set":{"time":int(time.time())}})
                ########################    
                c = DBclient.xljy.realtime.find({"mac":data_json["data"][0]["address"],"time":{"$lte":data_json["data"][0]["time"], "$gte":(data_json["data"][0]["time"]-240) }})
                c_list = list(c)
                c_count = c.count()
                if c_count == 0:
                    CursorMax = DBclient.xljy.realtime.aggregate([{"$match":{"mac":data_json["data"][0]["address"]}},{"$group":{"_id":"$mac","time_max":{"$max":"$time"}}}])
                    CursorMax_list = list(CursorMax)
                    time_max_before = CursorMax_list[0]["time_max"]
                    if ( len(CursorMax_list) != 0 ) and ( time_max_before != data_json["data"][0]["time"] - 300 ):
                        #insert history
                        history = DBclient.xljy.history.insert({"mac":data_json["data"][0]["address"],"start":time_max_before + 60,"end":data_json["data"][0]["time"] - 300})
                            
                if c_count == 5:
                    nothingtoupdate = 1
                else:
                    upload_flag = True
                    i = 5
                    t = 0
                    cc = None
                    for t in range(data_json["data"][0]["time"]-240,data_json["data"][0]["time"]+60,60):
                        for cc in c_list:
                            if cc["time"] == t:
                                upload_flag = False
                                break;
                            else:
                                upload_flag = True
                        if upload_flag:
                            if SendToRemoteCount(t, data_json["data"][0]["address"], data_json["data"][0]["counts"+str(i)], data_json["data"][0]["battery"]):
                                log.debug("insert realtime mac:%s  time=%d", data_json["data"][0]["address"], t)
                                DBclient.xljy.realtime.insert({"mac":data_json["data"][0]["address"], "time":t})
                        i = i - 1

            elif data_json["type"] == "history":
                DBclient.xljy.history0.insert(data_json["data"][0])
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
            log.debug("on_message:ERROR 002")
            #traceback.print_exception(*sys.exc_info(), file=HANDLE_LOG)
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
