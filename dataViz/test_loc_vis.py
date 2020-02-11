import multiprocessing # https://pymotw.com/2/multiprocessing/communication.html
# import openFace as of
#import bodySensors as bs
# import openBCI_receive as ob
# import btGSR_PPG as eda
# import recordVideo as rv
import numpy as np
import time
import os
from multiprocessing import Queue
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.console
from pyqtgraph.dockarea import *
import socket
import threading
from struct import *
import queue # needed for queue.empty exception since multiprocessing borrowns it from this library
from _thread import *
from wirelessDataCollection import runDataCollector
import sys
# first of all import the socket library
import socket

sys.path.insert(1, 'C:/dev/stm32-vive-position-sensor/Visualization')
from vive_pos_visualizer import run3D_visualizer

import json
import encryption as en

from PyQt5.QtWidgets import *

loc_visualizer_queue = Queue()

start_new_thread(run3D_visualizer, (loc_visualizer_queue,))

dx = 0
dy = 0
dz = 0

while(1):

    # # next create a socket object
    # s = socket.socket()
    #
    # # reserve a port on your computer in our
    # # case it is 12345 but it can be anything
    # port = port_loc_vis
    #
    # # Next bind to the port
    # # we have not typed any ip in the ip field
    # # instead we have inputted an empty string
    # # this makes the server listen to requests
    # # coming from other computers on the network
    # s.bind(('', port))
    #
    # # put the socket into listening mode
    # s.listen(5)
    #
    # # a forever loop until we interrupt it or
    # # an error occurs
    # while True:
    #     # Establish connection with client.
    #     c, addr = s.accept()
    #
    #     # Close the connection with the client
    #     c.close()



    time.sleep(1)

    dx += 1
    dy += 1
    dz += 1

    loc_visualizer_queue.put([dx, dy, dx, 0, 0])
    print("put: " + str(dx))