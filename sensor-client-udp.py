#!/usr/bin/python

import socket   #for sockets
import sys  #for exit
import random
import time
import argparse
import md5

from client_controller import protocol
timeout = .5
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()

# print 'Socket Created'

parser = argparse.ArgumentParser(description='Sensor TCP Client')
parser.add_argument('-s',"--server" , help="Host's ipv4 address", default='localhost')
parser.add_argument('-p',"--port" , help="Host's inbound port", default=8888, type=int)
parser.add_argument('-u',"--username" , help="Sensor's username", required=True)
parser.add_argument('-c',"--credential" , help="Sensor's credentials", required=True)
parser.add_argument('-r',"--reading" , help="Temperature reading", required=True, type=float)
args = vars(parser.parse_args())
host = args['server']
port = args['port']
username = args['username']
credential = args['credential']
temperature = args['reading']
s.settimeout(timeout)
try:
    remote_ip = socket.gethostbyname( host )
except socket.gaierror:
    #could not resolve
    print 'Hostname could not be resolved. Exiting'
    sys.exit()
addr = (host, port)
#Connect to remote server
# connected = False
# attempts = 0
# while connected is False and attempts < 5:
#     try:
#         attempts += 1
#         s.connect((remote_ip, port))
#         connected = True
#     except:
#         print "Server refused connection, trying again in 3 seconds..."
#         time.sleep(timeout)
# if attempts == 5:
#     print 'TCP Sensor Server might be down, try again later.'
#     sys.exit(1)
# print 'Socket Connected to ' + host + ' on ip ' + remote_ip

#Send temperature to remote server
success = False
STATE = protocol.AUTH
nonce = ""
average = ""
attempts = 0
while success is False and attempts < 5:
    try:
        if STATE == protocol.AUTH:
            message = username + "|AUTH"
            s.sendto(message, addr)
            reply = s.recv(4096)
            if reply.split(":")[0] == protocol.CHAL:
                STATE = protocol.CHAL
            elif reply == protocol.REFD:
                message = username + "|END"
                s.sendto(message, addr)
                success = True
                print "Authorization refused by server"
        elif STATE == protocol.CHAL:
            if reply.split(":")[0] == "CHAL":
                nonce = reply.split(":")[1]
                STATE = protocol.RESP
        elif STATE == protocol.RESP and nonce != "":
            message = username + "|RESP:" + md5.MD5(username + credential + nonce).hexdigest()
            s.sendto(message, addr)
            reply = s.recv(4096)
            # print reply
            if reply == "CONT":
                STATE = protocol.CONT
            else:
                message = username + "|END"
                chance = random.randint(0, 10)
                # print chance
                success = True
                print "Authorization refused by server"
                # if chance < 7:
                #     continue
                s.sendto(message, addr)
        elif STATE == protocol.CONT:
            message = username + "|TEMP:" + str(temperature)
            s.sendto(message, addr)
            reply = s.recv(4096)
            if reply.split(":")[0] == "AVG":
                average = reply.split(":")[1]
                success = True
            message = username + "|END"
            success = True
            s.sendto(message, addr)
        elif STATE == protocol.REFD:
            print "Authentication refused by server."


        attempts = 0
    except socket.timeout:
        print "UDP Timeout, resending..."
        attempts += 1
    except socket.error, exc:
        print "Socket error, trying again in 3 seconds..."
        print exc
        time.sleep(timeout)

if success is False:
    print "Server error"
    sys.exit(1)
else:
    print average


