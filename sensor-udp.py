#!/usr/bin/python

import socket   #for sockets
import sys      #for exit
import random   #for random challenge
import time     #for timestamp
import argparse
import md5
import datetime #for timestamp
import logging

logging.basicConfig()
logger = logging.getLogger("sensor-udp")

from client_controller import protocol
timeout = .5
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()

print 'Socket Created'

parser = argparse.ArgumentParser(description='Sensor TCP Client')
parser.add_argument('-s',"--server" , help="Host's ipv4 address", default='localhost', type=str)
parser.add_argument('-p',"--port" , help="Host's inbound port", default=8888, type=int)
parser.add_argument('-u',"--username" , help="Sensor's username", required=True, type=str)
parser.add_argument('-c',"--credential" , help="Sensor's credentials", required=True, type=str)
parser.add_argument('-r',"--reading" , help="Temperature reading", required=True, type=float)
parser.add_argument('-d', "--debug", help="Turn on debugging statements", action='store_true',  default=False)

args = vars(parser.parse_args())
if args['debug']:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
host = args['server']
port = args['port']
username = args['username']
credential = args['credential']
temperature = args['reading']
logger.debug(" Debug Mode On")
s.settimeout(timeout)
try:
    remote_ip = socket.gethostbyname( host )
except socket.gaierror:
    #could not resolve
    logger.debug('Hostname could not be resolved. Exiting')
    sys.exit()
addr = (host, port)

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
                success = True
                print "Authorization refused by server"
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
s.close()
if success is False:
    print "Server error"
    sys.exit(1)
else:
    reply = average
    avg = reply.split(",")[0]
    allavg = reply.split(",")[1]
    maxtemp = reply.split(",")[2]
    mintemp = reply.split(",")[3]
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%b %d %H:%M:%S')
    print "Sensor: " + username + " recorded: " + str(temperature) + " time: " \
          + timestamp + " sensorMin: " + str(mintemp) + " sensorMax: " + str(maxtemp) + " sensorAvg: " + str(avg) \
          + " allAvg: " + str(allavg)