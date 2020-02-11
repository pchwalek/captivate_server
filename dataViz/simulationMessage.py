# import zmq
import socket
import random
import sys
import time
import os
import subprocess
import numpy as np
import pandas as pd
import _thread
import atexit
import signal
import select
import multiprocessing
import queue  # needed for queue.empty exception since multiprocessing borrowns it from this library
from struct import *

# what port to listen on (defined within OpenFace C++ code)
port = 5555
addr = '127.0.0.1'

# define struct that is being received
captivate_header = ['blink_data', 'blink_tick_ms',
                    # 'temp_data', 'temp_tick_ms',
                    # 'inertial_data', 'intertial_tick_ms',
                    # 'pos_data', 'pos_tick_ms',
                    'tick_ms', 'epoch',
                    'system_epoch']

captivate_header_sizes = {'blink_data' : '100B',
                          'blink_tick_ms' : 'I',
                          # 'temp_data' : '10B',
                          # 'temp_tick_ms' : 'I',
                          # 'inertial_data' : '2B',
                          # 'intertial_tick_ms' : 'I',
                          # 'pos_data' : '3B',
                          # 'pos_tick_ms' : 'I',
                          'tick_ms' : 'I',
                          'epoch' : 'I'}

captive_total_header_types = ""
for _,val in captivate_header_sizes.items():
    captive_total_header_types = captive_total_header_types + val

test_msg = pack(captive_total_header_types,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
                12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
                12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
                12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                12, 45, 78)

random_list = ( ((np.random.rand(103) * 100)).astype(int)  ).tolist()
# random_msg = pack("%sB" % len(random_list), *random_list)


def Main():
    global addr, port

    host = socket.gethostname()

    # treat this as a client (the Captivate Dashboard is the server)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to server on local computer
    s.connect((host, port))

    msg_index = 0
    # message you send to server
    while True:
        # message sent to server
        print("sending message : " + str(msg_index))
        msg_index += 1

        # generate random message
        random_list = (((np.random.rand(103) * 100)).astype(int)).tolist()
        random_msg = pack("100BIII", *random_list)

        # send message
        s.send(random_msg)
        time.sleep(.1)

        # # messaga received from server
        # data = s.recv(1024)
        #
        # # print the received message
        # # here it would be a reverse of sent message
        # print('Received from the server :', str(data.decode('ascii')))
        #
        # # ask the client whether he wants to continue
        # ans = input('\nDo you want to continue(y/n) :')
        # if ans == 'y':
        #     continue
        # else:
        #     break
    # close the connection
    s.close()

if __name__ == '__main__':
    Main()









#     # open socket to connect to OpenFace
#     socket.connect("tcp://localhost:%s" % port)
#     socket.setsockopt(zmq.SUBSCRIBE, b'')
#
#
#
#
#
#
# # first of all import the socket library
# import socket
#
# # next create a socket object
# s = socket.socket()
# print "Socket successfully created"
#
# # reserve a port on your computer in our
# # case it is 12345 but it can be anything
# port = 12345
#
# # Next bind to the port
# # we have not typed any ip in the ip field
# # instead we have inputted an empty string
# # this makes the server listen to requests
# # coming from other computers on the network
# s.bind(('', port))
# print "socket binded to %s" % (port)
#
# # put the socket into listening mode
# s.listen(5)
# print "socket is listening"
#
# # a forever loop until we interrupt it or
# # an error occurs
# while True:
#     # Establish connection with client.
#     c, addr = s.accept()
#     print 'Got connection from', addr
#
#     # send a thank you message to the client.
#     c.send('Thank you for connecting')
#
#     # Close the connection with the client
#     c.close()