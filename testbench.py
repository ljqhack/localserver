import paho.mqtt.client as mqtt
import time, json,math
MQHOST = '127.0.0.1'
MQPORT = 1883

REALTIME = "UPLOAD/REALTIME"

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
    msg_realtime["data"] = [{"address":wristaddress,"time":t,"counts1":166,"counts2":166,"counts3":166,"counts4":166,"counts5":166,"battery":80}]
    json_msg = json.dumps(msg_realtime)
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
    #for i in range(1, 101, 1):
    #    msg = realtime_pack(INSCHOOL_HOST, WRISTBAND+ " " +str(i), time_wrist)
    #    client.publish(REALTIME, msg)
    #time.sleep(40)
    for i in range(1, 100, 1):
        msg = realtime_pack(OUTSCHOOL_HOST, WRISTBAND+ " " +str(i), time_wrist)
        print(msg)
        client.publish(REALTIME, msg)
        time.sleep(0.01)
        
    
def TestMain():
    print("start test localserver!")
    TeCase2()
    print("end test!!")


if __name__ == '__main__':
    TestMain()
