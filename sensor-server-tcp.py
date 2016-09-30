#!/usr/bin/python

import socket
import sys
from thread import *
from client_controller import *
import md5
import argparse
import csv
import random
import string

parser = argparse.ArgumentParser(description='Sensor TCP Client')
parser.add_argument('-p',"--port" , help="Host's inbound port", default=8888, type=int)
parser.add_argument('-f',"--csvfile" , help="Password CSV File", required=True)
args = vars(parser.parse_args())
csvfile = args['csvfile']
port = args['port']

HOST = ''   # Symbolic name meaning all available interfaces
# PORT = 8888 # Arbitrary non-privileged port
clients = {}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'
with open(csvfile, "rb") as clientfile:
    clientreader = csv.reader(clientfile, delimiter=",")
    for row in clientreader:
        clients[row[0]] = sensor_client(row[0], row[1])
#Bind socket to local host and port
try:
    s.bind((HOST, port))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket bind complete'
#Start listening on socket
s.listen(10)
print 'Socket now listening'

def total_average(client_dict):
    return sum([client.running_sum for _, client in client_dict.iteritems()])/sum([client.running_count for _, client in client_dict.iteritems()])

timeout = 1
#Function for handling connections. This will be used to create threads
def clientthread(conn, addr):
    # conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
    # client = sensor_client()
    # infinite loop so that function do not terminate and thread do not end.
    success = False
    STATE = protocol.AUTH
    username = ""
    while success is False:
        try:
            if STATE == protocol.AUTH:
                reply = conn.recv(4096)
                if reply == "AUTH":
                    STATE = protocol.CHAL
            elif STATE == protocol.CHAL:
                # Random String Generator from http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
                nonce = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
                message = "CHAL:" + nonce
                conn.sendall(message)
                reply = conn.recv(4096)
                if reply.split(":")[0] == "RESP":
                    if reply.split(":")[2] not in clients:
                        STATE = protocol.REFD
                    else:
                        md5hash = reply.split(":")[1]
                        localhash = md5.MD5(clients[reply.split(":")[2]].username + clients[reply.split(":")[2]].password + nonce).hexdigest()
                        if md5hash == localhash:
                            STATE = protocol.CONT
                            username = reply.split(":")[2]
                        else:
                            STATE = protocol.REFD
            elif STATE == protocol.CONT:
                message = "CONT"
                conn.sendall(message)
                reply = conn.recv(4096)
                if reply.split(":")[0] == "TEMP":
                    clients[username].update(float(reply.split(":")[1]))
                    STATE = protocol.TEMP
            elif STATE == protocol.TEMP:
                message = "AVG:" + str(clients[username].average()) + "," + str(total_average(clients))
                conn.sendall(message)
                success = True
            elif STATE == protocol.REFD:
                message = "REFD"
                conn.sendall(message)
                print "Authentication refused by server."
                break
        except socket.error, exc:
            print "Client ended connection." + str(exc)
            break
    print addr[0]+ ":" + str(addr[1]) + ' ended conversation.'
    conn.close()

#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    conn, addr = s.accept()
    print 'Connected with ' + addr[0] + ':' + str(addr[1])

    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    start_new_thread(clientthread ,(conn, addr))

s.close()