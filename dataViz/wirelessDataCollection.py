# import zmq
# import socket programming library
import socket

# import thread module
from _thread import *
import threading

import gc

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

import encryption as en

from collections import namedtuple

# print_lock = threading.Lock()
msgParserSem = threading.Semaphore()

# what port to listen on (defined within OpenFace C++ code)
port = 5555

host_name = socket.gethostname()
host = socket.gethostbyname(host_name)


# define struct that is being received
# captivate_header = ['blink_data', 'blink_tick_ms', 'blink_payload_ID',
#                     # 'temp_data', 'temp_tick_ms',
#                     # 'inertial_data', 'intertial_tick_ms',
#                     # 'pos_data', 'pos_tick_ms',
#                     'tick_ms', 'epoch',
#                     'system_epoch']

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
                          'epoch' ,
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

captivate_header_sizes = {'blink_data' : '100s',
                          'blink_tick_ms' : 'I',
                          'blink_payload_ID' : 'I',

                          'temple_temp' : 'H',
                          'temple_therm' : 'H',
                          'temple_tick_ms' : 'I',
                          'nose_temp' : 'H',
                          'nose_therm' : 'H',
                          'nose_tick_ms' : 'I',
                          'parsed_sec_tick_ms' : 'I',
                          'parsed_sec_epoch' : 'I',

                          'quatI' : 'f',
                          'quatJ' : 'f',
                          'quatK' : 'f',
                          'quatReal' : 'f',
                          'quatRadianAccuracy' : 'f',
                          'rot_tick_ms' : 'I',
                          'activityConfidence' : '9s',
                          'tick_ms_activity' : 'I',

                          'pos_x' : 'f',
                          'pos_y' : 'f',
                          'pos_z' : 'f',
                          'pos_accuracy' : 'f',
                          'tick_ms_pos' : 'I',
                          'pos_epoch' : 'I',

                          'tick_ms' : 'I',
                          'epoch' : 'I'}

# convert header fields to string for namedTuple creation in message parsing thread
captivate_labels_to_string = ""
index = 0
for key, val_ in captivate_header_sizes.items():
    captivate_labels_to_string = captivate_labels_to_string + key

    if( index < (len(captivate_header_sizes) - 1) ):
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
for _,val in captivate_header_sizes.items():
    captive_total_header_types = captive_total_header_types + val


# # https://github.com/TadasBaltrusaitis/OpenFace/wiki/Command-line-arguments
# OpenFace_Exec = "C:/dev/flow/project_flow/OpenFace/Release/FeatureExtraction"
# OpenFace_Model_CMU_Flag = "-mloc"
# OpenFace_Model_CMU = "C:/dev/flow/project_flow/OpenFace/Release/model/main_clnf_multi_pie.txt"
# OpenFace_QuietMode_Flag = '-q'
# OpenFace_Device_Flag = "-device"
# OpenFace_Device = '0'
# OpenFace_Grayscale = '0'
# OpenFace_CamWidth_Flag = "-cam_width"  # 640, 1920, 2560
# OpenFace_CamWidth = '1280'  # 1920, 1280
# OpenFace_CamHeight_Flag = "-cam_height"  # 480, 1080. 1440
# OpenFace_CamHeight = '720'  # 1080, 720

# # to visualize action units, add "-verbose"
# Commands = [OpenFace_Exec
#     , OpenFace_Device_Flag, OpenFace_Device
#                      #  ,OpenFace_Model_CMU_Flag, OpenFace_Model_CMU
#                      #   , OpenFace_QuietMode_Flag
#     , OpenFace_Grayscale
#                      # , "-verbose"
# #    , OpenFace_CamWidth_Flag
# #    , OpenFace_CamWidth
# #    , OpenFace_CamHeight_Flag
# #    , OpenFace_CamHeight
#                      ]

# where to save dataframe with stored values, including timestamps
# Save_Location = "C:/dev/glasses/dataViz/data/"

Save_Location = "data/"

Filetype = ".csv"

SAVE_CHECKPOINT_CNT=300

def saveFile(dataframe, filename, header=False):
    dataframe.iloc[0:].to_csv(filename, mode='a', index=False, header=header)

    dataframe.drop(dataframe.index, inplace=True)

class CaptivateData():

    def __init__(self):
        # instantiate dataFrame to store incoming packets

        self.header = captivate_header

        self.data = pd.DataFrame(columns=self.header)
        self.checkpoint_data = pd.DataFrame(columns=self.header)
        self.log_cycle = 0

        self.filename = "captivate_msg_log_"

        # instantiate dataFrames for each sensor modality
        self.sensors = {}
        self.sensors['blink'] = BlinkData()
        self.sensors['therm'] = ThermData()
        self.sensors['inertial'] = InertialData()
        self.sensors['pos'] = PosData()


        self.prev_location = np.array((0, 0))
        self.current_location = np.array((0, 0))
        self.face_movement = 0

        # self.prev_gaze_vector = np.array((1,0,0))
        # self.current_gaze_vector = np.array((1,0,0))
        # self.gaze_angle_change = 0

        self.start_time = time.time()

        self.save_location = Save_Location

        self.start_point = 0


        # queues where latest messages get passed to update plots
        self.blink_queue = 0
        self.temp_queue = 0
        self.pos_queue = 0
        self.inertial_queue = 0

        self.first_append = 1

        self.packet_cnt = 0



    def add_queues(self, blink_queue, temp_queue, pos_queue, inertial_queue):
        self.blink_queue = blink_queue
        self.temp_queue = temp_queue
        self.inertial_queue = inertial_queue
        self.pos_queue = pos_queue


        self.sensors['blink'].set_queue(blink_queue)
        self.sensors['therm'].set_queue(temp_queue)
        self.sensors['inertial'].set_queue(inertial_queue)
        self.sensors['pos'].set_queue(pos_queue)



    def set_sample_rate(self, sensor, new_sample_rate):
        # add new data with UNIX timestamp
        self.sensors[sensor].set_sample_rate(new_sample_rate)

    def add_data(self, sample):
        # add new data with UNIX timestamp
        #print(sample.values())
        # test = list(sample.items())
        self.data.loc[len(self.data)] = list(sample.items()) + [time.time()]
        # self.calculate_face_movement()

        # print("temple:\t" + str(sample['temple_temp']) + "\ttemple therm:\t" + str(sample['temple_therm']))
        self.packet_cnt += 1
        print("  CAPTIVATE LOGGER : packet received : " + str(self.packet_cnt))

        # for key, val in self.sensors.items():
        #     self.sensors[key].add_data(sample)

        if self.data.shape[0] > SAVE_CHECKPOINT_CNT:
            self.checkpoint_save_data()

    def checkpoint_save_data(self):
        if (self.log_cycle == 0):
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 1
        else:
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 0

        if(self.first_append):
            self.first_append = 0

            start_new_thread(saveFile, (self.checkpoint_datswa, self.save_location + self.filename + str(int(self.start_time)) + Filetype, True,))
            # self.data.iloc[self.start_point:].to_csv(self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #                                         mode='a', index=False, header=True)
        else:
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=False)

        # for key, val in self.sensors.items():
        #     self.sensors[key].checkpoint_save_data()

        # clear dataframe
        # self.checkpoint_data.drop(self.data.index, inplace=True)

    def save_data(self):
        #self.openface_data.to_csv(self.save_location + Filename + str(int(self.start_time)) + Filetype, index=False)
        print(self.save_location + self.filename + str(int(self.start_time)) + Filetype)
        # start_new_thread(saveFile, (
        #     self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
        self.data.iloc[self.start_point:].to_csv(self.save_location + self.filename + str(int(self.start_time)) + Filetype, mode='a', index=False, header=False)

        # for key, val in self.sensors.items():
        #     self.sensors[key].save_data()

    def set_save_location(self, new_directory):
        print(self.save_location)
        self.save_location = new_directory

    def return_last_sample(self):
        return self.data.iloc[-1]

    # def print_blinking(self):
    #     # note: only looking at left eye
    #
    #     # print if blinking
    #     if (self.openface_data.iloc[-1]['AU45_c'] == 1):
    #         if self.past_blink == False:
    #             self.past_blink = True
    #             self.blink_cnt = self.blink_cnt + 1
    #             print("blink: " + str(self.blink_cnt))
    #     elif self.past_blink == True:
    #         self.past_blink = False
    #
    # def calculate_face_movement(self):
    #     # use tip of nose in 3D space to calculate face movement
    #     self.current_location = np.array((self.openface_data.iloc[-1]['X_30'], self.openface_data.iloc[-1]['Y_30']))
    #     self.face_movement = np.linalg.norm(self.current_location - self.prev_location)
    #     self.prev_location = np.copy(self.current_location)

    def set_save_point(self):
        self.start_point = len(self.openface_data.index)


class BlinkData():

    def __init__(self):
        # # instantiate dataframe to store data
        # self.data = pd.DataFrame(columns=blink_sub_header)

        # instantiate dataFrame to store incoming packets
        # self.data_0 = pd.DataFrame(columns=blink_sub_header)
        # self.data_1 = pd.DataFrame(columns=blink_sub_header)

        self.header = blink_sub_header

        self.data = pd.DataFrame(columns=self.header)
        self.checkpoint_data = pd.DataFrame(columns=self.header)
        self.log_cycle = 0

        # default settings
        self.sample_rate = 1000
        self.sample_period = 1. / self.sample_rate

        # blink tracker
        self.blink_cnt = 0
        self.past_blink = False

        self.prev_location = np.array((0, 0))
        self.current_location = np.array((0, 0))
        self.face_movement = 0

        self.filename = 'captivate_blink_log_'
        # self.prev_gaze_vector = np.array((1,0,0))
        # self.current_gaze_vector = np.array((1,0,0))
        # self.gaze_angle_change = 0

        self.start_time = time.time()

        self.save_location = Save_Location

        self.start_point = 0

        self.blink_queue = 0

        self.first_append = 1

    def set_queue(self, _queue):
        self.blink_queue = _queue

    def set_sample_rate(self, new_sample_rate):
        # add new data with UNIX timestamp
        self.sample_rate = new_sample_rate
        self.sample_period = 1. / self.sample_rate

    def calc_tick_ms_sample(self, tick_ms, sample_len):

        return

    def checkpoint_save_data(self):
        if (self.log_cycle == 0):
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 1
        else:
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 0

        if (self.first_append):
            self.first_append = 0
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, True,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=True)
        else:
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=False)

        # clear dataframe
        # self.checkpoint_data.drop(self.data.index, inplace=True)

    def add_data(self, msg_unpacked):
        # create matrix of data with columns : blink sample , tick_ms that sample was taken , approx. system epoch time

        # (1)... create an array of unpacked blink data
        data_unpacked = array.array('B', msg_unpacked['blink_data']).tolist()

        # (2)... create an array of len(received sample length) with interpolated tick_ms times
        data_size = len(data_unpacked)
        subtractor = np.flip(np.arange(0, data_size) * self.sample_period)
        tick_ms = np.ones(data_size) * msg_unpacked['blink_tick_ms']
        tick_ms = tick_ms - subtractor

        # (2)... create an array of len(received sample length) with interpolated captivate's RTC times
        epoch_times = np.ones(data_size) * msg_unpacked['epoch'] # create array of epoch times
        epoch_correction = (tick_ms - msg_unpacked['tick_ms']) / 1000. # find the offset in seconds that you need to correct for
        epoch_times = epoch_times + epoch_correction # apply offsets

        # (4)... create numpy matrix of new data
        new_data = np.array([data_unpacked, tick_ms, epoch_times]).T

        # (5)... append
        self.data = self.data.append(pd.DataFrame(new_data, columns=blink_sub_header))

        # (6)... send to visualizer
        self.blink_queue.put(np.array([data_unpacked, tick_ms]))



    def save_data(self):
        #self.openface_data.to_csv(self.save_location + Filename + str(int(self.start_time)) + Filetype, index=False)
        print("  CAPTIVATE LOGGER : saving blink data")
        print("  CAPTIVATE LOGGER : blink file : " + self.save_location + self.filename + str(int(self.start_time)) + Filetype)
        # start_new_thread(saveFile, (
        #     self.data.copy(deep=True), self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
        self.data.iloc[self.start_point:].to_csv(self.save_location + self.filename + str(int(self.start_time)) + Filetype, mode='a', index=False, header=False)

    def set_save_location(self, new_directory):
        print(self.save_location)
        self.save_location = new_directory

    def return_last_sample(self):
        return self.data.iloc[-1]

    def set_save_point(self):
        self.start_point = len(self.openface_data.index)

class ThermData():

    def __init__(self):
        # instantiate dataframe to store data
        # self.data = pd.DataFrame(columns=therm_sub_header)

        # instantiate dataFrame to store incoming packets
        # self.data_0 = pd.DataFrame(columns=therm_sub_header)
        # self.data_1 = pd.DataFrame(columns=therm_sub_header)

        self.header = therm_sub_header

        self.data = pd.DataFrame(columns=self.header)
        self.checkpoint_data = pd.DataFrame(columns=self.header)
        self.log_cycle = 0

        # # default settings
        # self.sample_rate = 1000
        # self.sample_period = 1. / self.sample_rate

        # # blink tracker
        # self.blink_cnt = 0
        # self.past_blink = False

        self.prev_location = np.array((0, 0))
        self.current_location = np.array((0, 0))
        self.face_movement = 0

        self.filename = 'captivate_temp_log_'
        # self.prev_gaze_vector = np.array((1,0,0))
        # self.current_gaze_vector = np.array((1,0,0))
        # self.gaze_angle_change = 0

        self.start_time = time.time()

        self.save_location = Save_Location

        self.start_point = 0

        self.queue = 0

        self.first_append = 1

    def set_queue(self, _queue):
        self.queue = _queue

    # def set_sample_rate(self, new_sample_rate):
    #     # add new data with UNIX timestamp
    #     self.sample_rate = new_sample_rate
    #     self.sample_period = 1. / self.sample_rate

    def calc_tick_ms_sample(self, tick_ms, sample_len):

        return

    def checkpoint_save_data(self):
        if (self.log_cycle == 0):
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 1
        else:
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 0

        if (self.first_append):
            self.first_append = 0
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, True,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=True)
        else:
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=False)

        # clear dataframe
        # self.checkpoint_data.drop(self.data.index, inplace=True)

    def add_data(self, msg_unpacked):
        # create matrix of data with columns : blink sample , tick_ms that sample was taken , approx. system epoch time

        # # (1)... create an array of unpacked blink data
        # data_unpacked = array.array('B', msg_unpacked['blink_data']).tolist()
        #
        # # (2)... create an array of len(received sample length) with interpolated tick_ms times
        # data_size = len(data_unpacked)
        # subtractor = np.flip(np.arange(0, data_size) * self.sample_period)
        # tick_ms = np.ones(data_size) * msg_unpacked['blink_tick_ms']
        # tick_ms = tick_ms - subtractor
        #
        # # (2)... create an array of len(received sample length) with interpolated captivate's RTC times
        # epoch_times = np.ones(data_size) * msg_unpacked['epoch'] # create array of epoch times
        # epoch_correction = (tick_ms - msg_unpacked['tick_ms']) / 1000. # find the offset in seconds that you need to correct for
        # epoch_times = epoch_times + epoch_correction # apply offsets

        # todo: link epoch

        # (4)... create numpy matrix of new data
        therm_data = {key: msg_unpacked[key] for key in therm_parse_sub_header}
        therm_data['nose_epoch'] = (msg_unpacked['nose_tick_ms'] - msg_unpacked['parsed_sec_tick_ms'])/1000. + msg_unpacked['parsed_sec_epoch']
        therm_data['temple_epoch'] = (msg_unpacked['temple_tick_ms'] - msg_unpacked['parsed_sec_tick_ms'])/1000. + msg_unpacked['parsed_sec_epoch']
        new_data = np.array(list(therm_data.values())).T

        # print("temple:\t" + str(msg_unpacked['temple_temp']) + "\ttemple therm:\t" + str(msg_unpacked['temple_therm']))

        # (5)... append
        self.data = self.data.append(pd.DataFrame([new_data], columns=therm_sub_header))

        # (6)... send to visualizer
        # print("therm adding to queue")
        self.queue.put(np.array([msg_unpacked['nose_temp'],
                                      msg_unpacked['temple_temp'],
                                      msg_unpacked['temple_tick_ms']]))


    def save_data(self):
        #self.openface_data.to_csv(self.save_location + Filename + str(int(self.start_time)) + Filetype, index=False)
        print("  CAPTIVATE LOGGER : saving temp data")
        print("  CAPTIVATE LOGGER : thermo file : " + self.save_location + self.filename + str(int(self.start_time)) + Filetype)
        self.data.iloc[self.start_point:].to_csv(self.save_location + self.filename + str(int(self.start_time)) + Filetype,mode='a',  index=False, header=False)
        # start_new_thread(saveFile, (
        #     self.data.copy(deep=True), self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))


    def set_save_location(self, new_directory):
        print(self.save_location)
        self.save_location = new_directory

    def return_last_sample(self):
        return self.data.iloc[-1]

    def set_save_point(self):
        self.start_point = len(self.openface_data.index)

class InertialData():

    def __init__(self):
        # instantiate dataframe to store data
        # self.data = pd.DataFrame(columns=inertial_sub_header)

        # instantiate dataFrame to store incoming packets
        # self.data_0 = pd.DataFrame(columns=inertial_sub_header)
        # self.data_1 = pd.DataFrame(columns=inertial_sub_header)

        self.header = inertial_sub_header

        self.data = pd.DataFrame(columns=self.header)
        self.checkpoint_data = pd.DataFrame(columns=self.header)
        self.log_cycle = 0

        # # default settings
        # self.sample_rate = 1000
        # self.sample_period = 1. / self.sample_rate

        # # blink tracker
        # self.blink_cnt = 0
        # self.past_blink = False

        self.prev_location = np.array((0, 0))
        self.current_location = np.array((0, 0))
        self.face_movement = 0

        self.filename = 'captivate_inertial_log_'
        # self.prev_gaze_vector = np.array((1,0,0))
        # self.current_gaze_vector = np.array((1,0,0))
        # self.gaze_angle_change = 0

        self.start_time = time.time()

        self.save_location = Save_Location

        self.start_point = 0

        self.inertial_queue = 0

        self.first_append = 1

    def set_queue(self, _queue):
        self.inertial_queue = _queue

    # def set_sample_rate(self, new_sample_rate):
    #     # add new data with UNIX timestamp
    #     self.sample_rate = new_sample_rate
    #     self.sample_period = 1. / self.sample_rate

    def calc_tick_ms_sample(self, tick_ms, sample_len):

        return

    def checkpoint_save_data(self):
        if (self.log_cycle == 0):
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 1
        else:
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 0

        if (self.first_append):
            self.first_append = 0
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, True,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=True)
        else:
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=False)

        # clear dataframe
        # self.checkpoint_data.drop(self.data.index, inplace=True)

    def add_data(self, msg_unpacked):
        # create matrix of data with columns : blink sample , tick_ms that sample was taken , approx. system epoch time

        # # (1)... create an array of unpacked blink data
        # data_unpacked = array.array('B', msg_unpacked['blink_data']).tolist()
        #
        # # (2)... create an array of len(received sample length) with interpolated tick_ms times
        # data_size = len(data_unpacked)
        # subtractor = np.flip(np.arange(0, data_size) * self.sample_period)
        # tick_ms = np.ones(data_size) * msg_unpacked['blink_tick_ms']
        # tick_ms = tick_ms - subtractor
        #
        # # (2)... create an array of len(received sample length) with interpolated captivate's RTC times
        # epoch_times = np.ones(data_size) * msg_unpacked['epoch'] # create array of epoch times
        # epoch_correction = (tick_ms - msg_unpacked['tick_ms']) / 1000. # find the offset in seconds that you need to correct for
        # epoch_times = epoch_times + epoch_correction # apply offsets

        # todo: link epoch

        # (4)... create numpy matrix of new data
        inertial_data = {key: msg_unpacked[key] for key in inertial_parse_sub_header}
        inertial_data['rot_epoch'] = (msg_unpacked['rot_tick_ms'] - msg_unpacked['parsed_sec_tick_ms'])/1000. + msg_unpacked['parsed_sec_epoch']
        new_data = np.array(list(inertial_data.values())).T

        # (5)... append
        self.data = self.data.append(pd.DataFrame([new_data], columns=inertial_sub_header))

        # print(msg_unpacked['quatRadianAccuracy'])

        # (6)... send to visualizer
        activity_unpacked = array.array('B', msg_unpacked['activityConfidence']).tolist()
        self.inertial_queue.put(np.array([msg_unpacked['quatReal'],
                                          msg_unpacked['quatI'],
                                          msg_unpacked['quatJ'],
                                          msg_unpacked['quatK'],
                                          activity_unpacked]))

    def save_data(self):
        #self.openface_data.to_csv(self.save_location + Filename + str(int(self.start_time)) + Filetype, index=False)
        print("  CAPTIVATE LOGGER : saving inertial data")
        print("  CAPTIVATE LOGGER : intertial file : " + self.save_location + self.filename + str(int(self.start_time)) + Filetype)
        # start_new_thread(saveFile, (
        #     self.data.copy(deep=True), self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
        self.data.iloc[self.start_point:].to_csv(self.save_location + self.filename + str(int(self.start_time)) + Filetype,mode='a',  index=False, header=False)

    def set_save_location(self, new_directory):
        print(self.save_location)
        self.save_location = new_directory

    def return_last_sample(self):
        return self.data.iloc[-1]

    def set_save_point(self):
        self.start_point = len(self.openface_data.index)

class PosData():

    def __init__(self):
        # instantiate dataframe to store data
        # self.data = pd.DataFrame(columns=pos_sub_header)

        # instantiate dataFrame to store incoming packets
        self.header = pos_sub_header

        self.data = pd.DataFrame(columns=self.header)
        self.checkpoint_data = pd.DataFrame(columns=self.header)
        self.log_cycle = 0

        # # default settings
        # self.sample_rate = 1000
        # self.sample_period = 1. / self.sample_rate

        # # blink tracker
        # self.blink_cnt = 0
        # self.past_blink = False

        self.prev_location = np.array((0, 0))
        self.current_location = np.array((0, 0))
        self.face_movement = 0

        self.filename = 'captivate_pos_log_'
        # self.prev_gaze_vector = np.array((1,0,0))
        # self.current_gaze_vector = np.array((1,0,0))
        # self.gaze_angle_change = 0

        self.start_time = time.time()

        self.save_location = Save_Location

        self.start_point = 0

        self.inertial_queue = 0

        self.first_append = 1

    def set_queue(self, _queue):
        self.inertial_queue = _queue

    # def set_sample_rate(self, new_sample_rate):
    #     # add new data with UNIX timestamp
    #     self.sample_rate = new_sample_rate
    #     self.sample_period = 1. / self.sample_rate

    def calc_tick_ms_sample(self, tick_ms, sample_len):

        return

    def checkpoint_save_data(self):
        if (self.log_cycle == 0):
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 1
        else:
            self.checkpoint_data.drop(self.checkpoint_data.index, inplace=True)
            gc.collect()
            self.checkpoint_data = self.data
            self.data = pd.DataFrame(columns=self.header)
            self.log_cycle = 0

        if (self.first_append):
            self.first_append = 0
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, True,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=True)
        else:
            start_new_thread(saveFile, (
                self.checkpoint_data, self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
            # self.data.iloc[self.start_point:].to_csv(
            #     self.save_location + self.filename + str(int(self.start_time)) + Filetype,
            #     mode='a', index=False, header=False)

        # # clear dataframe
        # self.checkpoint_data.drop(self.data.index, inplace=True)

    def add_data(self, msg_unpacked):
        # create matrix of data with columns : blink sample , tick_ms that sample was taken , approx. system epoch time

        # # (1)... create an array of unpacked blink data
        # data_unpacked = array.array('B', msg_unpacked['blink_data']).tolist()
        #
        # # (2)... create an array of len(received sample length) with interpolated tick_ms times
        # data_size = len(data_unpacked)
        # subtractor = np.flip(np.arange(0, data_size) * self.sample_period)
        # tick_ms = np.ones(data_size) * msg_unpacked['blink_tick_ms']
        # tick_ms = tick_ms - subtractor
        #
        # # (2)... create an array of len(received sample length) with interpolated captivate's RTC times
        # epoch_times = np.ones(data_size) * msg_unpacked['epoch'] # create array of epoch times
        # epoch_correction = (tick_ms - msg_unpacked['tick_ms']) / 1000. # find the offset in seconds that you need to correct for
        # epoch_times = epoch_times + epoch_correction # apply offsets

        # todo: link epoch

        # (4)... create numpy matrix of new data
        pos_data = {key: msg_unpacked[key] for key in pos_parse_sub_header}
        pos_data['parsed_pos_epoch'] = (msg_unpacked['tick_ms_pos'] - msg_unpacked['parsed_sec_tick_ms'])/1000. + msg_unpacked['parsed_sec_epoch']
        new_data = np.array(list(pos_data.values())).T

        # (5)... append
        self.data = self.data.append(pd.DataFrame([new_data], columns=pos_sub_header))


        # (6)... send to visualizer
        self.inertial_queue.put(np.array([msg_unpacked['pos_x'],
                                          msg_unpacked['pos_y'],
                                          msg_unpacked['pos_z'],
                                          msg_unpacked['pos_accuracy'],
                                          msg_unpacked['tick_ms_pos']]))

    def save_data(self):
        #self.openface_data.to_csv(self.save_location + Filename + str(int(self.start_time)) + Filetype, index=False)
        print("  CAPTIVATE LOGGER : saving position data")
        print("  CAPTIVATE LOGGER : position file : " + self.save_location + self.filename + str(int(self.start_time)) + Filetype)
        # start_new_thread(saveFile, (
        #     self.data.copy(deep=True), self.save_location + self.filename + str(int(self.start_time)) + Filetype, False,))
        self.data.iloc[self.start_point:].to_csv(self.save_location + self.filename + str(int(self.start_time)) + Filetype, mode='a', index=False, header=False)

    def set_save_location(self, new_directory):
        print(self.save_location)
        self.save_location = new_directory

    def return_last_sample(self):
        return self.data.iloc[-1]

    def set_save_point(self):
        self.start_point = len(self.openface_data.index)

# thread fuction
def msgReceiveThread(c, msg_queue, enable_dongle_br=0):

    global captivate_labels_to_string

    while True:

        # data received from client
        try:
            data = c.recv(1024)
            if not data:
                # print('Bye')

                # lock released on exit
                #print_lock.release()
                break

            # msg_unpacked = unpack(captive_total_header_types, data)
            # print("received something")
            msg_unpacked = namedtuple('msg_unpacked', captivate_labels_to_string)

            if(enable_dongle_br==0):
                data_decrypted = en.do_decrypt(data)
                # print(len(data_decrypted))
                msg_unpacked = msg_unpacked._make(unpack(captive_total_header_types, data_decrypted))
            else:
                msg_unpacked = msg_unpacked._make(unpack(captive_total_header_types, data))

            try:
                msg_queue.put_nowait(msg_unpacked._asdict())
            except queue.Full:
                continue
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

def msgParser(msg_queue, msgParserSem, blink_queue, temp_queue, pos_queue, inertial_queue):

    # instantiate face response class
    capData = CaptivateData()
    capData.add_queues( blink_queue, temp_queue, pos_queue, inertial_queue)
    print(" MSG PARSER ACTIVE")
    while True:
        try:
            # print("msg parser waiting")
            msg_unpacked = msg_queue.get(timeout=10)
            # print("cap data unpackaed queue get")
            capData.add_data(msg_unpacked)
        #
        # except KeyboardInterrupt:
        #     break
            if msgParserSem.acquire(blocking=False):
                break

        except queue.Empty:
            if msgParserSem.acquire(blocking=False):
                break
            continue
    # print(" MSG PARSER INACTIVE")
    capData.save_data()



def runDataCollector(system_sem, blink_queue, temp_queue, pos_queue, inertial_queue, enable_dongle_br = 0, queue_log = 0, alert_queue = 0):


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
    if(enable_dongle_br==0):
        s.bind((host, port))
    else:
        s.bind(('localhost', port))
    s.settimeout(1)
    timeout_counter = 0

    # start queue for message passing between threads
    msg_queue = Queue(maxsize=400)

    # start message parser thread
    msgParserSem.acquire(blocking=False)
    parser = threading.Thread(target=msgParser, args=(msg_queue, msgParserSem, blink_queue, temp_queue, pos_queue, inertial_queue))
    parser.setDaemon(True)
    parser.start()

    # put the socket into listening mode
    s.listen(5)
    print("  CAPTIVATE LOGGER : socket is listening")


    while True:
        try:
            # establish connection with client
            c, addr = s.accept()

            # lock acquired by client
            #print_lock.acquire()
            #TODO: logger always reconnects per each sample received
            # print('  CAPTIVATE LOGGER : Connected to :', addr[0], ':', addr[1])

            # Start a new thread and return its identifier
            receiver_thread = threading.Thread(target=msgReceiveThread, args=(c, msg_queue, enable_dongle_br,))
            receiver_thread.start()

            # user will free a semaphore if "stop stream" is selected in the console
            if system_sem.acquire(blocking=False):
                system_sem.release()
                print('  CAPTIVATE LOGGER : STOPPING DATA STREAM')
                # stop message parser
                msgParserSem.release()

                print('  CAPTIVATE LOGGER : WAIT FOR THREADS TO FINISH!')
                # wait for parser to join back
                time.sleep(.5)
                parser.join()

                break
        except KeyboardInterrupt:

            print('  CAPTIVATE LOGGER : INTERRUPT RECEIVED')


            print('  CAPTIVATE LOGGER : WAIT FOR THREADS TO FINISH!')
            msgParserSem.release()
            time.sleep(2)
            parser.join()
            break

        except socket.timeout as e:

            # user will free a semaphore if "stop stream" is selected in the console
            if system_sem.acquire(blocking=False):
                system_sem.release()

                print('  CAPTIVATE LOGGER : STOPPING DATA STREAM')
                # stop message parser
                msgParserSem.release()

                print('  CAPTIVATE LOGGER : WAIT FOR THREADS TO FINISH!')
                # wait for parser to join back
                time.sleep(.5)
                parser.join()

                break

            continue


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
    # SystemExit()

    sys.exit()
    return

if __name__ == '__main__':
    runDataCollector()