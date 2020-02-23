import time
import queue
import multiprocessing
import threading
import socket

import encryption as en

import sys
import threading

import time

import sys
sys.path.append('/home/pi/captivate/dataViz/CoAPthon3')
# sys.path.append('C:\dev\glasses\dataViz\CoAPthon3')


from struct import *
import json
import netifaces as ni

import ipaddress as ip_fcns

from collections import namedtuple
# from vive_pos_visualizer import *

import struct
from serial import Serial

PORT_NAME = "COM70"
BAUDRATE = 115200
READ_TIMEOUT = 15
DELIMITER = b'\n\n'

captivate_header = ['blink_data',
                    'blink_tick_ms',
                    'blink_payload_ID',
                    'temple_temp',
                    'temple_therm',
                    'temple_tick_ms',
                    'nose_temp',
                    'nose_therm',
                    'nose_tick_ms',
                    'parsed_sec_tick_ms',
                    'parsed_sec_epoch',

                    'quatI',
                    'quatJ',
                    'quatK',
                    'quatReal',
                    'quatRadianAccuracy',
                    'rot_tick_ms',
                    'activityConfidence',
                    'tick_ms_activity',

                    'pos_x',
                    'pos_y',
                    'pos_z',
                    'pos_accuracy',
                    'tick_ms_pos',
                    'pos_epoch',

                    'tick_ms',
                    'epoch',
                    'system_epoch']

pos_parse_sub_header = ['pos_x',
                        'pos_y',
                        'pos_z',
                        'pos_accuracy',
                        'tick_ms_pos',
                        'pos_epoch']

pos_sub_header = ['pos_x',
                  'pos_y',
                  'pos_z',
                  'pos_accuracy',
                  'time_ms_pos',
                  'pos_epoch',
                  'parsed_pos_epoch']

blink_sub_header = ['blink_data', 'blink_tick_ms', 'epoch']

therm_parse_sub_header = ['temple_temp',
                          'temple_therm',
                          'temple_tick_ms',
                          'nose_temp',
                          'nose_therm',
                          'nose_tick_ms']

therm_sub_header = ['temple_temp',
                    'temple_therm',
                    'temple_tick_ms',
                    'nose_temp',
                    'nose_therm',
                    'nose_tick_ms',
                    'nose_epoch',
                    'temple_epoch']

inertial_parse_sub_header = ['quatI',
                             'quatJ',
                             'quatK',
                             'quatReal',
                             'quatRadianAccuracy',
                             'rot_tick_ms',
                             'activityConfidence',
                             'tick_ms_activity']

inertial_sub_header = ['quatI',
                       'quatJ',
                       'quatK',
                       'quatReal',
                       'quatRadianAccuracy',
                       'rot_tick_ms',
                       'activityConfidence',
                       'tick_ms_activity',
                       'rot_epoch']

captivate_header_sizes = {'blink_data': '100s',
                          'blink_tick_ms': 'I',
                          'blink_payload_ID': 'I',

                          'temple_temp': 'H',
                          'temple_therm': 'H',
                          'temple_tick_ms': 'I',
                          'nose_temp': 'H',
                          'nose_therm': 'H',
                          'nose_tick_ms': 'I',
                          'parsed_sec_tick_ms': 'I',
                          'parsed_sec_epoch': 'I',

                          'quatI': 'f',
                          'quatJ': 'f',
                          'quatK': 'f',
                          'quatReal': 'f',
                          'quatRadianAccuracy': 'f',
                          'rot_tick_ms': 'I',
                          'activityConfidence': '9s',
                          'tick_ms_activity': 'I',

                          'pos_x': 'f',
                          'pos_y': 'f',
                          'pos_z': 'f',
                          'pos_accuracy': 'f',
                          'tick_ms_pos': 'I',
                          'pos_epoch': 'I',

                          'tick_ms': 'I',
                          'epoch': 'I'}

# convert header fields to string for namedTuple creation in message parsing thread
captivate_labels_to_string = ""
index = 0
for key, val_ in captivate_header_sizes.items():
    captivate_labels_to_string = captivate_labels_to_string + key

    if (index < (len(captivate_header_sizes) - 1)):
        captivate_labels_to_string = captivate_labels_to_string + " "
    index += 1

# captivate_header_index = {'blink_data' : 100,
#                           'blink_tick_ms' : 101,
#                           # 'temp_data' : '10B',
#                           # 'temp_tick_ms' : 'I',
#                           # 'inertial_data' : '2B',
#                           # 'intertial_tick_ms' : 'I',
#                           # 'pos_data' : '3B',
#                           # 'pos_tick_ms' : 'I',
#                           'tick_ms' : 'I',
#                           'epoch' : 'I'}

captive_total_header_types = ""
for _, val in captivate_header_sizes.items():
    captive_total_header_types = captive_total_header_types + val

import re
def get_serial_data(port, unicode=False):
    serial_byte_data = port.read_until(terminator=DELIMITER)
    serial_byte_data = serial_byte_data.rstrip(b'\n\n')
    serial_byte_data = serial_byte_data[2:]
    # msg_unpacked = namedtuple('msg_unpacked', captivate_labels_to_string)
    # # print(len(data_decrypted))
    # msg_unpacked = msg_unpacked._make(unpack(captive_total_header_types, serial_byte_data))._asdict()
    # print(msg_unpacked)

    if(len(serial_byte_data)==204):
        # msg_unpacked = namedtuple('msg_unpacked', captivate_labels_to_string)
        # # print(len(data_decrypted))
        # msg_unpacked = msg_unpacked._make(unpack(captive_total_header_types, serial_byte_data))._asdict()
        # print(msg_unpacked)

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # connect to data collector
            s.connect(('localhost', 5555))
            # encrypt message to be sent
            # if this is a message to set leds
            # s.send(bytearray(message, 'utf-8'))
            s.send(serial_byte_data)
        except socket.error as msg:
            print("Caught exception socket.error : " + str(msg))
        finally:
            s.close()


    # if unicode:
    #     serial_unicode_data = serial_byte_data.decode(encoding='utf-8')
    #     return serial_unicode_data
    # else:
    #     return serial_byte_data


def process_command(port):
    input_command = get_serial_data(port, unicode=True)

    # if input_command == 'JPEG':
    #     port.write(ACK)
    #     process_jpeg_data(port)
    # elif input_command == 'CSV':
    #     port.write(ACK)
    #     process_csv_data(port)
    # else:
    #     pass



def main():

    try:

        port = Serial(port=PORT_NAME, baudrate=BAUDRATE, timeout=READ_TIMEOUT)
        port.write(struct.pack('bbbbbb',1,1,0,0,1,0))
    except Exception:
        print(f'\033[31munable to open serial port {PORT_NAME}\033[39m')
    # try:
    while True:
        if port.in_waiting > 0:
            process_command(port)
        time.sleep(0.05)
    # except:
    #     port.write(struct.pack('bbbbbb', 0, 0, 0, 0, 0, 0))


if __name__ == "__main__":
    main()