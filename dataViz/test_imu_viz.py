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

# sys.path.insert(1, 'C:/dev/stm32-vive-position-sensor/Visualization')
# from vive_pos_visualizer import run3D_visualizer

import json
import encryption as en

from PyQt5.QtWidgets import *

def send_imu_to_vis(quat_w ,quat_i ,quat_j ,quat_k):

    string_quat = str('w') + str(quat_w) + str('w')
    string_quat += str('a') + str(quat_i) + str('a')
    string_quat += str('b') + str(quat_j) + str('b')
    string_quat += str('c') + str(quat_k) + str('c')

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(('localhost', 5005))
            string_quat = string_quat.encode()
            # packet = pack("fff", x, y, z)
            s.sendall(string_quat)
        except socket.error as msg:
            print("Caught exception socket.error : " + str(msg))
        finally:
            s.close()



if __name__ == '__main__':
    while(True):
        print("send")
        send_imu_to_vis(1,0,0,1)
        time.sleep(3)
        print("send")
        send_imu_to_vis(0, 0, 0, 1)
        time.sleep(3)
        print("send")
        send_imu_to_vis(0, 1, 0, 1)
        time.sleep(3)
        print("send")
        send_imu_to_vis(0, 0, 1, 1)
        time.sleep(3)