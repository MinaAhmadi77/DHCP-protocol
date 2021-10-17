#!/usr/bin/python3
import math
import socket
import operator
from _thread import *
from netaddr import IPNetwork
import sys 
from ipaddress import IPv4Address,IPv4Network,ip_address, ip_network
import ipaddress
import json
from readJson import *
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

class dhcpServer:
    def __init__(self, port):   
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        self.hostname = get_local_ip()
        print(self.hostname)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1000)
        self.leaseTime = lease_time
        self.macs = {}
        self.old_macs = {}
        # information to be sent back
        self.Ips = []
        self.netAddress = "default"
        self.broadAddress = "default"
        self.DNSGateway  = "default"
        self.setData()
    
    def setData(self):
        print("DHCP is working with " + pool_mode + " mode")
        print("***************************************************************")
        if (pool_mode == "subnet"): 
            net = ipaddress.ip_network(ip_block+"/" + subnet_mask, strict=False)
            self.netAddress = net.network_address
            self.broadAddress = net.broadcast_address
            self.Ips = [str(ip) for ip in ipaddress.IPv4Network(net)]
            self.Ips.pop(0)
            self.DNSGateway = net.network_address

        elif(pool_mode == "range"):
            start = ip_address(from_)
            end = ip_address(to_)
            while start <= end:
                self.Ips.append(str(start))
                start += 1
        else:
            print("config error!")
            try:
                self.Ips.remove(reservation_list[rs])
                self.old_macs[rs] = reservation_list[rs]
            except:
                print("Cannot reserve IP, IP does not exist!")


    def dhcpDiscover(self, conn):
        mac_address = conn.recv(50).decode('utf-8')
        if mac_address in black_list:
            print("Client is blocked!!")
            fullStatus = 2
            conn.send(str(fullStatus).encode('utf-8'))
            return 0


        try:
            client = self.macs[mac_address]
        except KeyError:
            client = "unallocated"

        if client == "unallocated":
            if 0 == len(self.Ips):
                fullStatus = 1
                print ("subnet is full")
                conn.send(str(fullStatus).encode('utf-8'))
                return 0
            elif mac_address in reservation_list.keys():
                print(reservation_list[mac_address])
                ipToAssign = reservation_list[mac_address]

            else:
                if mac_address in self.old_macs:
                    ipToAssign = self.old_macs[mac_address]
                else:
                    ipToAssign = self.Ips[0]
            fullStatus = 0
            conn.send(str(fullStatus).encode('utf-8'))
            self.dhcpOffer(ipToAssign, mac_address, conn)
        
    def dhcpOffer(self, ip, mac_address, conn):
        Ack = 0
        while not Ack:
            conn.send(ip.encode('utf-8'))
            Ack = int(conn.recv(1).decode('utf-8'))
        Ack = 0
        while not Ack:
            conn.send(str(self.netAddress).encode('utf-8'))
            Ack = int(conn.recv(1).decode('utf-8'))
        Ack = 0
        while not Ack:  
            conn.send(str(self.broadAddress).encode('utf-8'))
            Ack = int(conn.recv(1).decode('utf-8'))
        Ack = 0
        while not Ack:
            conn.send(str(self.DNSGateway).encode('utf-8'))
            Ack = int(conn.recv(1).decode('utf-8'))
        self.dhcpRequest(ip, mac_address, conn)

    def dhcpRequest(self, ip, mac_address, conn):

        assignedIp = conn.recv(100).decode('utf-8')
        if assignedIp == ip:
            self.dhcpAck(1, mac_address, ip, conn)
        else:
            self.dhcpAck(0, mac_address, ip, conn)

    def dhcpAck(self, ack, mac_address, ip, conn):

        if ack:
            conn.send('ACK'.encode('utf-8'))
            if "Cannot" in str(ip):
                print ("cannot allocate Ip to this client!")
            else:
                for i in range(0, len(self.Ips)):
                    if self.Ips[i] == ip:
                        self.Ips.remove(ip)
                        break
                print ("serving " + str(mac_address) + " " + str(ip) + " !")
                conn.send(str(self.leaseTime).encode('utf-8'))
                try:
                    x = conn.recv(1).decode('utf-8')
                    timeout = int(x)
                except:
                    timeout = 0
                if timeout:
                    self.Ips.append(ip)
                    self.old_macs[mac_address] = ip
                    print (str(mac_address) + " connection closed !")
        else:
            conn.send('NACK'.encode('utf-8'))
            self.dhcpDiscover(conn)


if __name__ == "__main__":
    
    server = dhcpServer(port=int(sys.argv[1]))
    while True:
        conn, addr = server.socket.accept()
        start_new_thread(server.dhcpDiscover,(conn,))        
