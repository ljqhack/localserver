import json
from pymongo import MongoClient
import time
import math
from threading import Timer
import urllib.request, urllib.parse
import socket,threading
RemoteServer = 'http://xiangliang.airm2m.com/xiangliang_web/api.php?m=index'
CMDSEND = '&a=sendstudesmove'
CMDCHECK = '&a=sendattendance'
UPSTATUS = '&a=basestationstatus'

params_dict = {"ctime":int(time.time()), "mac":"FF:FF:FF:FF:FF:FF", "status":1}
params = urllib.parse.urlencode(params_dict).encode('utf-8')
f = urllib.request.urlopen(RemoteServer+UPSTATUS, params, timeout = 20)
jstr=f.read().decode('utf-8-sig')
print(str(jstr))

'''
a=b'333'
print(a.decode('utf-8'))
def UdpServer():
    address = ('', 33333)  
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    s.bind(address)  
    while True:
        data, addr = s.recvfrom(2048)  
        if not data:  
            print("client has exist")
            break
        s.sendto(b'hello',addr)
        print(data)
        print(addr)
    print("close")  
    s.close()
udp = threading.Thread(target = UdpServer)
#udp.setDaemon(True)
udp.start()

while True:
    time.sleep(1)

'''









print(time.time())
RemoteServer = 'http://test.brotherphp.com/xiangliang_web/api.php?m=index'
CMDSEND = '&a=sendstudesmove'
cmd = '&a=sendattendance'
params_dict = {"stimestamp":int(time.time()), "mac":"d4:ae:68:68:64:6e", "state":1}
params = urllib.parse.urlencode(params_dict).encode('utf-8')
f = urllib.request.urlopen(RemoteServer+cmd, params, timeout = 20)
jstr=f.read().decode('utf-8-sig')
print(jstr)

while True:
    print("ha ha ha")
    time.sleep(0.7)

h="a"
c = {}

def fun(ss):
    print(ss)
t= Timer(2,fun,["333344"])
c[h] = t
c[h].start()
#c[h].cancel()
c["b"] = Timer(2,fun,["555566666"])
c["b"].start()
while True:
    time.sleep(0.2)
    #if c[h].isAlive():
    #print("alive")
    if "b" in c:
        print("ddss")
    else:
        print("tt")
print(abs(-300/33))

DBHOST = '127.0.0.1'
DBPORT = 27017

DBclient = MongoClient(DBHOST, DBPORT)
cursor = DBclient.xljy.realtime.find_one({"test":"test"})
print(cursor["test"])

ISOTIMEFORMAT='%Y-%m-%d %X'
print(time.strftime( ISOTIMEFORMAT, time.localtime()))

a = b'{"type":"real_time","hostaddress":"aa:bb:cc:dd", "routertime":1437616495, "rssi":20, "data":[{"address":"aa:bb:cc", "time":1437616495, "counts":166}]}'
a_str = a.decode("utf-8")

try:
    data_json = json.loads(a.decode('utf-8'))
except:
    print("ERROR")

DBclient.xljy.sign_table.update_one( {"mac":data_json["data"][0]["address"]}, {'$set':{"rssi0":data_json["rssi"], "rssi1":0, "rssi2":0, "rssi3":0, "time":data_json["routertime"]}})
DBclient.xljy.history.delete_many({"rssi":20})

DBclient.xljy.sign_table.update_one({"mac":"AA:BB:CC:31"}, {"$set":{"rssi0":32}})
                                    
