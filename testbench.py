import paho.mqtt.client as mqtt

MQHOST = '127.0.0.1'
MQPORT = 1883

REALTIME = "UPLOAD/REALTIME"
msg = '{"type":"real_time","hostaddress":"aa:bb:cc:dd", "routertime":1437616495 , "rssi":20, "data":[{"address":"aa:bb:cc", "time":1437616495, "counts1":166, "counts2":166,"counts3":166,"counts4":166,"counts5":166,"battery":80}]}'

def TestFunc():
    print("start test localserver!")
    client = mqtt.Client()
    client.connect(MQHOST, MQPORT, 60)
    client.Publish(REALTIME, msg)
