import sys, time
from gevent.server import StreamServer
from gevent import monkey
monkey.patch_socket()
import gevent
import logging

#LOGFILE = "E:\localserver.log"
logging.basicConfig(level=logging.DEBUG)
logging.debug('START DEBUG LOG')

HOST = '127.0.0.1'
PORT = 15555

def handle(socket, address):
    logging.debug('New connection from %s:%s' % address)
    while True:
        try:
            data = socket.recv(1024)
            socket.send(bytearray([0x31,0x32,0x33]))
            print(data)
            if not data:
                logging.debug("client disconnected")
                break
        except Exception:
            logging.DEBUG("ERROR")
    

if __name__ == '__main__':
    server = StreamServer(( HOST, PORT), handle)
    try:
        server.serve_forever()
    finally:
        pass

