# import zmq
# import socket programming library
import socket

# import thread module
from _thread import *
import threading

import random
import sys
import time
import os
import subprocess
import numpy as np
import pandas as pd
# import _thread
import atexit
import signal
import select
from queue import Queue
import multiprocessing
import queue  # needed for queue.empty exception since multiprocessing borrowns it from this library
from struct import *
import array as array
import netifaces as ni

from collections import namedtuple

# print_lock = threading.Lock()
msgParserSem = threading.Semaphore()

# what port to listen on (defined within OpenFace C++ code)
port = 5554
host = ""

# thread fuction
def msgReceiveThread(c, msg_queue):

    global captivate_labels_to_string

    prev_message = ""

    while True:

        # data received from client
        try:
            data = c.recv(1024)
            if not data:
                print('Bye')

                # lock released on exit
                #print_lock.release()
                break
                
            # print(data)

            # msg_unpacked = unpack(captive_total_header_types, data)
            print("prev_message :" + prev_message )
            if prev_message == 'set_led':
                print("led_message")
                msg_unpacked = unpack('18B14x', data)
            else:
                msg_unpacked = data.decode("utf-8")

            prev_message = msg_unpacked

            msg_queue.put(msg_unpacked)

            #print(data)

        except KeyboardInterrupt:
            break

        # # reverse the given string from client
        # data = data[::-1]
        #
        # # send back reversed string to client
        # c.send(data)

        # connection closed
    c.close()

def msgParser(msg_queue, msgParserSem):

    while True:
        try:
            if msgParserSem.acquire(blocking=False):
                break
            msg_unpacked = msg_queue.get(timeout=1000)
            print(msg_unpacked)
            # capData.add_data(msg_unpacked)
        #
        # except KeyboardInterrupt:
        #     break

        except queue.Empty:
            continue

def runDataCollector(queue_log = 0, alert_queue = 0):
    # try:
    #     process_return = subprocess.Popen(Commands, shell=True,
    #                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    # except subprocess.CalledProcessError as e:
    #     raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    # # create zmq socket for transmission of packet from COAP server to this application
    # context = zmq.Context()
    # socket = context.socket(zmq.SUB)

    global host, port

    print("")
    print("  CAPTIVATE LOGGER : Collecting updates...")

    # bind socket to start server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    # s.settimeout(1)
    timeout_counter = 0

    # start queue for message passing between threads
    msg_queue = Queue()

    # put the socket into listening mode
    s.listen(5)
    print("  CAPTIVATE LOGGER : socket is listening")

    # start message parser thread
    msgParserSem.acquire()
    parser = threading.Thread(target=msgParser, args=(msg_queue, msgParserSem,))
    parser.setDaemon(False)
    parser.start()

    while True:
        try:
            # establish connection with client
            c, addr = s.accept()

            # lock acquired by client
            #print_lock.acquire()
            print('  CAPTIVATE LOGGER : Connected to :', addr[0], ':', addr[1])

            # Start a new thread and return its identifier
            start_new_thread(msgReceiveThread, (c, msg_queue, ))
        except KeyboardInterrupt:

            print('  CAPTIVATE LOGGER : INTERRUPT RECEIVED')


            print('  CAPTIVATE LOGGER : WAIT FOR THREADS TO FINISH!')
            msgParserSem.release()
            time.sleep(2)
            parser.join()
            break
        # except socket.timeout as e:
        #     continue


        # #  try:
        # # timeout if no message received within one second
        # socks = dict(poller.poll(1000))
        #
        # # if message received, grab it
        # if socks:
        #     if socks.get(socket) == zmq.POLLIN:
        #
        #         # parse out message
        #         msg = socket.recv(zmq.NOBLOCK)
        #
        #         msg_unpacked = unpack(captive_total_header_types, msg)
        #         print msg_unpacked
        #
        #         # msg = msg.decode('ascii')
        #         # msg = msg.replace(" ", "")
        #         # msg = msg.rstrip('\n')
        #         # msg = msg.split(",")
        #         #
        #         # # convert strings to floats
        #         # msg = [float(i) for i in msg]
        #         #
        #         # # put OpenFace data into dataframe
        #         # face_data.add_data(msg)
        #         #
        #         # # push current results into queue
        #         # queue_log.put(face_data.return_last_sample())
        #         #
        #         # # print if blinking
        #         # face_data.print_blinking()
        #         #
        #         # # check if app has been notified to close
        #         # try:
        #         #     notification = alert_queue.get(block=False)
        #         # except queue.Empty:
        #         #     # Handle empty queue here
        #         #     pass
        #         # else:
        #         #     if notification[0] == "s":
        #         #         face_data.set_save_point()
        #         #     elif notification[0] == "e":
        #         #         print('  CAPTIVATE LOGGER : SAVING DATA!')
        #         #         face_data.set_save_location(notification[1])
        #         #         face_data.save_data()
        #         #     elif notification[0] == "q":
        #         #         print('  CAPTIVATE LOGGER : Quitting')
        #         #         face_data.set_save_location(notification[1])
        #         #         # # save data
        #         #         # print('  OPEN_FACE : SAVING DATA!')
        #         #         # face_data.save_data()
        #         #         # exit()
        #         #         break
        #
        #
        #     else:
        #         print("error: message timeout")

        # except KeyboardInterrupt:
        #     print('OPEN_FACE : INTERRUPT RECEIVED')
        #     break

    # save data

    # close socket
    print('  CAPTIVATE LOGGER : CLOSING SOCKET!')
    s.close()

    # print('  CAPTIVATE LOGGER : KILLING TASK!')


    print('  CAPTIVATE LOGGER : EMPTY QUEUES!')
    while 1:
        try:
            msg_queue.get_nowait()
        except queue.Empty:
            break

    print('  CAPTIVATE LOGGER : ALL DONE!')
    return

if __name__ == '__main__':
    runDataCollector()