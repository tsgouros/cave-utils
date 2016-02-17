#!/usr/bin/env python

# Listens on a set of ports, forwards telnet connections to pjcontrol
# script to send commands to a specific projector.
#


import socket, threading, subprocess, logging, re

HOST = '192.168.160.'
#HOST = '127.0.0.1'
PORT = 5450

# Object to hold the details of a socket connection.
class sskt():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen(4)

        print "listening on ", self.host, ":" , self.port

    def accept(self):
        return self.s.accept()

# A threading object that actually listens at a port and forwards the
# connection to pjcontrol.  The threads here are so this can take
# commands from multiple connections, though that is probably not
# useful in this context, and I haven't really tested it, either.
class projChat(threading.Thread):
    def __init__(self, (socket,address), lock, clients, projNumber):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address= address
        self.projNumber = projNumber
        self.lock = lock
        self.clients = clients

        logging.basicConfig(filename='/tmp/projd.log',
                            format='{0} proj{1:02d}: %(asctime)s :%(message)s'.format(self.address[0], self.projNumber),
                            datefmt='%m/%d/%Y %I:%M:%S %p',
                            level=logging.DEBUG)


    def run(self):
        self.lock.acquire()
        self.clients.append(self)
        self.lock.release()

        print '%s:%s connected.' % self.address
        while True:
            data = self.socket.recv(1024)
            if not data:
                break
            for c in self.clients:

                # fix string
                if '.off ' in data:
                    data = data.replace(".off ", ".offset ")
                if 'bright ' in data:
                    data = data.replace("bright", "brightness")

                logging.info(data.rstrip('\n\r') + '>')

                out = subprocess.check_output(["/gpfs/runtime/opt/cave-utils/yurt/bin/pjcontrol-raw", 
                                               "{0:02d}".format(self.projNumber),
                                               "raw {0}".format(data)])

                logging.info("OP " + out.rstrip('\n\r') + '<')
                #logging.info("OP " + out + '<')

                c.socket.send("OP " + out)
        self.socket.close()
        print '%s:%s disconnected.' % self.address
        self.lock.acquire()
        self.clients.remove(self)
        self.lock.release()

# This makes a thread dedicated a specific projector and IP.  The
# 'host' in this case is just the last number in the IP address.
class projChats(threading.Thread):
    def __init__(self, host, proj):
        threading.Thread.__init__(self)

        self.clients = [] #list of clients connected
        self.lock = threading.Lock()
        self.host = HOST + "{0:03d}".format(host)
        self.proj = proj

        self.skt = sskt(self.host, PORT)

    def run(self):
        while True: # wait for socket to connect
            # send socket to chatserver and start monitoring
            projChat(self.skt.accept(), self.lock, self.clients, self.proj).start()

#for i in range(0,68):
#         projChats(101 + i, i).start()

projChats(100,38).start()
projChats(101,39).start()
projChats(102,40).start()
projChats(103,41).start()
projChats(104,42).start()
projChats(105,43).start()
