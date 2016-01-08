import paho.mqtt.client as mqtt
from pymongo import MongoClient
import time, json,math
MQHOST = '127.0.0.1'
MQPORT = 1883
DBHOST = '127.0.0.1'
DBPORT = 27017

REALTIME = "UPLOAD/REALTIME"
HISTORY = "UPLOAD/HISTORY"

INSCHOOL_HOST = "06:0C:43:76:20:08"
OUTSCHOOL_HOST = "06:0C:43:76:20:0c"
NORMAL_HOST = "DF:0C:43:76:20:0c"
WRISTBAND = "F1:11:11:11:11:12"

time_wrist = 1451474100

def realtime_pack(hostaddress, wristaddress, t):
    msg_realtime = {}
    msg_realtime["type"] = "real_time"
    msg_realtime["hostaddress"] = hostaddress
    msg_realtime["routertime"] = int(time.time())
    msg_realtime["rssi"] = -50
    d = {"address":wristaddress,"time":t,"counts1":166,"counts2":166,"counts3":166,"counts4":166,"counts5":166,"battery":80}
    msg_realtime["data"] = [d]
    json_msg = json.dumps(msg_realtime)
    return json_msg
def history_pack(watchaddress, start, end):
    msg_history = {}
    msg_history["type"] = "history"
    msg_history["watchaddress"] = watchaddress
    msg_history["start"] = start
    msg_history["end"] = end
    msg_history["data"] = []
    i = 0
    for i in range(start, end + 60, 60):
        msg_history["data"].append(15)
    json_msg = json.dumps(msg_history)
    return json_msg

def TeCase1():
    client = mqtt.Client()
    client.connect(MQHOST, MQPORT, 60)
    client.loop_start()
    #normal_host
    msg = realtime_pack(NORMAL_HOST, WRISTBAND, time_wrist)
    client.publish(REALTIME, msg)
    client.publish(REALTIME, msg)
    #normal_host  t+300
    msg = realtime_pack(NORMAL_HOST, WRISTBAND, time_wrist+300)
    client.publish(REALTIME, msg)

    #normal_host  t+900
    msg = realtime_pack(NORMAL_HOST, WRISTBAND, time_wrist+900)
    client.publish(REALTIME, msg)

    #normal_host  t+1260
    msg = realtime_pack(NORMAL_HOST, WRISTBAND, time_wrist+1260)
    client.publish(REALTIME, msg)
    
    #inschool_host
    msg = realtime_pack(INSCHOOL_HOST, WRISTBAND, time_wrist+1320)
    client.publish(REALTIME, msg)
    client.publish(REALTIME, msg)

#sign and leave test
def TeCase2():
    client = mqtt.Client()
    client.connect(MQHOST, MQPORT, 60)
    client.loop_start()
    i = 0
    j = 0
    for j in range(1, 5, 1):
        for i in range(1, 5, 1):
            msg = realtime_pack(INSCHOOL_HOST, WRISTBAND+ " " +str(i), int(time.time()))
            client.publish(REALTIME, msg)
            time.sleep(0.01)
        time.sleep(5)
    for j in range(1, 100, 1):
        for i in range(1, 3, 1):
            msg = realtime_pack(INSCHOOL_HOST, WRISTBAND+ " " +str(i), time_wrist)
            client.publish(REALTIME, msg)
            time.sleep(0.01)
        time.sleep(5)
    time.sleep(5)
    '''
    for i in range(1, 6, 1):
        msg = realtime_pack(OUTSCHOOL_HOST, WRISTBAND+ " " +str(i), time_wrist)
        print(msg)
        client.publish(REALTIME, msg)
        time.sleep(0.01)
    '''
        
#history
def TeCase3():
    client = mqtt.Client()
    client.connect(MQHOST, MQPORT, 60)
    client.loop_start()
    
    DBclient = MongoClient(DBHOST, DBPORT)
    h = {"mac":WRISTBAND, "start":time_wrist, "starttoend":[time_wrist,time_wrist + 600]}
    DBclient.xljy.history.insert(h)
    
    msg = history_pack(WRISTBAND, time_wrist, time_wrist + 600)
    print(msg)
    client.publish(HISTORY, msg)
    time.sleep(2)
    ret = DBclient.xljy.history.find({"mac":WRISTBAND})
    if len(list(ret)) == 0:
        print("test success!!")

    
def TestMain():
    print("start test localserver!")
    #TeCase1()
    TeCase2()
    #TeCase3()
    print("end test!!")


if __name__ == '__main__':
    TestMain()
