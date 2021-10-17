#!/usr/bin/python3
import sys
import time
import socket
from readJson import *
import random
import multiprocessing
import os

rets =[-1, -1]
jobs = []

def info():
    return os.getpid()

def get_local_ip():
    import socket
    """Try to determine the local IP address of the machine."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        return sock.getsockname()[0]
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return '127.0.0.1'
    finally:
        sock.close()
class dhcpClient:
    ''' client requests methods for a connection to dhcp Server '''
    def __init__(self, port, mac, IPHost, event, pid, index):
        global rets
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientPort = port
        self.hostname = IPHost
        try:
            self.clientSocket.connect((self.hostname, self.clientPort))
            self.connection = True
        except:
            print("Server is not responding!")
            self.connection = False
        self.mac = mac
        self.backoof_backoff = 120
        self.P = 10
        self.event = event
        self.leaseTime = 0
        self.pid = pid
        self.index = index
    def clientDiscover(self):
        self.clientSocket.send(self.mac.encode('utf-8'))
        R = random.uniform(0, 1)
        wait = 2*R*self.P
        self.P = self.P + 2
        fullStatus = int(self.clientSocket.recv(1).decode('utf_8'))
        if fullStatus==1:
            print ("Subnet is full")
            if (wait < self.backoof_backoff):
                print("We are waiting ...")
                time.sleep(int(wait))
                self.clientDiscover()
            else:
                return 0

        elif fullStatus == 2:
            print ("You are blocked!!")
            return 0
        else:
            print("Getting IP offers ...")
            self.clientOffer()

    def clientOffer(self):   
        assignedIp = '' 
        while not assignedIp:
            assignedIp = self.clientSocket.recv(100).decode('utf_8')
            self.clientSocket.send(str(1).encode('utf-8'))
        self.ip =  assignedIp
        # recieve Network Address
        assignedNetworkAddress = ''
        while not assignedNetworkAddress:
            assignedNetworkAddress = self.clientSocket.recv(100).decode('utf_8')
            self.clientSocket.send(str(1).encode('utf-8'))
        self.networkAddress = assignedNetworkAddress
        # recieve BroadCast Address

        assignedBroadCastAddress = ''
        while not assignedBroadCastAddress:
            assignedBroadCastAddress = self.clientSocket.recv(100).decode('utf_8')
            self.clientSocket.send(str(1).encode('utf-8'))
        self.broadcastAddress = assignedBroadCastAddress
        assignedDNSGateway = ''
        while not assignedDNSGateway:
            assignedDNSGateway = self.clientSocket.recv(100).decode('utf_8')
            self.clientSocket.send(str(1).encode('utf-8'))
        self.DNS = assignedDNSGateway
        self.gateWay = assignedDNSGateway
        self.clientRequest(assignedIp)

    def clientRequest(self, ip):
        ''' send back the IP address sent by dhcp Server
            for verification of proper communication channel '''
        self.clientSocket.send(ip.encode('utf_8'))
        self.clientAck(ip)

    def clientAck(self, ip):
        global rets
        ''' receive the acknowledgment sent by dhcp Server '''
        ack = self.clientSocket.recv(4).decode('utf_8')
        if ack == "ACK":
            print("I Got an IP:")
            print ("IP:", self.ip)
            print ("Network:",self.networkAddress)
            print ("broadcastAddress: ",self.broadcastAddress)
            print ("DNS Address", self.DNS)
            print ("Gateway:", self.gateWay)

            #if "Cannot" in str(self.ip): 
                #print ("cannot connect to this Network")
            self.leaseTime = int(self.clientSocket.recv(10).decode('utf-8'))
            print(self.index, rets)
            rets[self.index] = self.pid
            self.event.set()
            time.sleep(self.leaseTime)
            self.clientSocket.send(str(1).encode('utf-8'))
            self.clientSocket.close()
        else:
            self.clientDiscover()
        

def job(event, port , mac , ip, i):
    global rets
    pid = info()
    client = dhcpClient(port , mac , ip, event, pid, i)
    if client.connection:
        client.clientDiscover()
    else:
        return 

    return 
if __name__ == "__main__":
    if len(sys.argv) == 3:
        port = int(sys.argv[2])
        mac = sys.argv[1]
        ip_0 = get_local_ip()
        ip_1 = "192.168.1.10"
        event = multiprocessing.Event()
        for i in range(2):
            if i == 0:
                print("Requesting on server", ip_0)
                p = multiprocessing.Process(target=job,args=(event,port, mac, ip_0,i ))
                jobs.append(p)
            else:
                print("Requesting on server", ip_1)
                p = multiprocessing.Process(target=job,args=(event,port, mac, ip_1,i ))
                jobs.append(p)
        jobs[0].start()
        time.sleep(10)
        jobs[1].start()
        while True:
            if event.is_set():
                print ("Exiting all dhcp request processes.")
                for index, i in enumerate(jobs):
                    if i.pid != rets[index]:
                        i.terminate()
                break
            time.sleep(1)
    else:
        print ("Give proper number of argument ( eg: ./dhcpClient.py MAC-ADDRESS server_port)")
