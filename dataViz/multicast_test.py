import socket
import struct

import errno

from struct import *
import json
import netifaces as ni


# Initialise socket for IPv6 datagrams
sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

sock.setsockopt(socket.SOL_SOCKET, 25, str("wpan0" + '\0').encode('utf-8'))

# Allows address to be reused
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Binds to all interfaces on the given port
MCAST_GRP = str(ni.ifaddresses('wpan0')[10][0]['addr'])
sock.bind(("::", 5683))

# Allow messages from this socket to loop back for development
sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)

# Construct message for joining multicast group
mreq = struct.pack("16s15s".encode('utf-8'), socket.inet_pton(socket.AF_INET6, "ff03::1"), (chr(0) * 16).encode('utf-8'))
sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

while True:
    data, addr = sock.recvfrom(1024)
    print(addr)
    print(data)

