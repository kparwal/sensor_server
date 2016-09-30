#!/usr/bin/python
import socket
import sys
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
clients = {}
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print 'Socket created'
with open(csvfile, "rb") as clientfile:
    clientreader = csv.reader(clientfile, delimiter=",")
    for row in clientreader:
        clients[row[0]] = sensor_client(row[0], row[1])
#Bind socket to local host and port
try:
    sock.bind((HOST, port))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket bind complete'

def total_average(client_dict):
    return sum([client.running_sum for _, client in client_dict.iteritems()])/sum([client.running_count for _, client in client_dict.iteritems()])

timeout = 1
state_machine = {}
nonce_dict = {}
conversations = 0
while 1:
    if conversations == 0:
        sock.settimeout(None)
    else:
        sock.settimeout(timeout)
    # print "conversations" + str(conversations)
    reply, client_addr = sock.recvfrom(4096)
    username = reply.split('|')[0]
    reply = reply.split("|")[1]
    if username not in state_machine and username in clients:
        state_machine[username] = protocol.AUTH
    elif username not in clients:
        sock.sendto(protocol.REFD, client_addr)
        if reply == protocol.END:
            print "Authentication refused by server."
        continue
    STATE = state_machine[username]
    message = ""
    # print state_machine
    # print reply
    try:
        if STATE == protocol.AUTH and reply == protocol.AUTH:
            # Random String Generator from http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
            conversations += 1
            print "Speaking with " + str(client_addr)
            nonce_dict[username] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
            message = "CHAL:" + nonce_dict[username]
            STATE = protocol.RESP
            sock.sendto(message, client_addr)
        elif STATE == protocol.RESP:
            if username not in clients:
                STATE = protocol.END
                print "Authentication refused by server."
            elif reply.split(":")[0] == protocol.RESP:
                md5hash = reply.split(":")[1]
                localhash = md5.MD5(username + clients[username].password + nonce_dict[username]).hexdigest()
                if md5hash == localhash:
                    STATE = protocol.CONT
                else:
                    STATE = protocol.END
                    conversations -= 1
                    print "Authentication refused by server."
            message = STATE
            # chance = random.randint(0, 10)
            # print chance
            # if chance < 5:
            #     continue
            sock.sendto(message, client_addr)
        elif STATE == protocol.CONT:
            clients[username].update(float(reply.split(":")[1]))
            message = "AVG:" + str(clients[username].average()) + "," + str(total_average(clients))
            STATE = protocol.END
            conversations -= 1
            sock.sendto(message, client_addr)
        elif STATE == protocol.END:
            STATE = protocol.AUTH
        state_machine[username] = STATE
    except socket.timeout:
        print "UDP Time out, resending..."
        sock.sendto(message, client_addr)
    except socket.error, exc:
        print "Client ended connection." + str(exc)
