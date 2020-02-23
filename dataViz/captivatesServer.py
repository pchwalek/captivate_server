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


from coapthon import defines
from coapthon.resources.resource import Resource
from coapthon.server.coap import CoAP
from coapthon.client.helperclient import HelperClient
from _thread import start_new_thread
from exampleresources import DebugResource
import errno

from struct import *
import json
import netifaces as ni

import ipaddress as ip_fcns

from collections import namedtuple
from lights_controller import *
from vive_pos_visualizer import *

TIMEOUT_ON_MSG = 2
LIGHTS_TIMEOUT_TIME = 3 # twenty seconds


# todo: visualizer and/or data collector need a way of receiving ip table

# create empty ip table
networkList = {}



def ipaddressToByteString(addr):

    addr_class = ip_fcns.IPv6Address(addr)
    byte_string = addr_class.packed
    return byte_string

def syncMessage(epoch, send_IP=0):

    ip = ipaddressToByteString(ni.ifaddresses('wpan0')[10][0]['addr'])
    epoch_string = pack('q', epoch)

    # print(ip)
    # print(epoch_string)
    # print("message length : " + len(ip + epoch_string))
    # print("message ip: " + str(ip))
    return ip + epoch_string

def networkAddrHandler(import_queue, export_queue, reset_sem, pass_table_sem):

    # create empty ip table
    global networkList

    while True:
        try:
            ip_addr, node_type, description, UID = import_queue.get(timeout=1)

            print("  got ip to update table : " + str(UID))
            # print("  current table : " + str(networkList))

            # associate a timestamp of when ip address was added
            #   note: if it already exists, timestamp is refreshed
            networkList[UID] = (ip_addr, node_type, time.time(), description)

            print("  new table : " + str(networkList))
            # print(networkList)
            # check if its requested to pass the current table
            if pass_table_sem.acquire(blocking=False):
                export_queue.put(networkList)

            # check if ip_addr table is requested to be reset
            if reset_sem.acquire(blocking=False):
                networkList = {}

        except queue.Empty:

            # check if its requested to pass the current table
            if pass_table_sem.acquire(blocking=False):
                export_queue.put(networkList)

            # check if ip_addr table is requested to be reset
            if reset_sem.acquire(blocking=False):
                networkList = {}

            continue

        except:
            print(" network address handler received unexpected exception : " + str(sys.exc_info()[0]))
            continue

def postMessageNodeThread(active_threads_sem, ip_address, coap_path, message, port, timeout=5, no_response=True):

    global networkList

    # grab semaphore if available
    active_threads_sem.acquire()

    # print("Sending message to : " + str(ip_address) + "\t" + "coap_path : " + str(coap_path))

    # send message to client
    client = HelperClient(server=(ip_address, port))
    # response = client.post(coap_path, message, timeout=timeout)
    # print(" DEBUG: sending to : " + str(coap_path) + '\t' + str(message))
    response = client.put(coap_path, message, timeout=timeout, no_response=no_response)
    client.stop()

    # if checking if device is still on network
    if coap_path == "devInfo":
        # if no response received, remove from IP table
        if response is None:
            del networkList[ip_address]

    print("Sent message to : " + str(ip_address) + "\t" + "coap_path : " + str(coap_path))

    # release semaphore when complete
    active_threads_sem.release()


def getMessageNodeThread(active_threads_sem, ip_address, coap_path, port, timeout=5, no_response=True):

    global networkList

    # grab semaphore if available
    active_threads_sem.acquire()

    # print("Sending message to : " + str(ip_address) + "\t" + "coap_path : " + str(coap_path))

    # send message to client
    client = HelperClient(server=(ip_address, port))
    # response = client.post(coap_path, message, timeout=timeout)
    # print(" DEBUG: sending to : " + str(coap_path) + '\t' + str(message))
    # response = client.observe(coap_path, timeout=10, no_response=False, callback=notifyResponse)
    response = client.get_non(coap_path, timeout=timeout, no_response=False)

    # try:
    #     print("TRYYYYYYY")
    #     print(response)
    # except:
    #     print("EXCEPTION")
    #     pass

    client.stop()

    # # if checking if device is still on network
    # if coap_path == "devInfo":
    #     # if no response received, remove from IP table
    #     if response is None:
    #         del networkList[ip_address]

    print("Sent request to : " + str(ip_address) + "\t" + "coap_path : " + str(coap_path))

    # release semaphore when complete
    active_threads_sem.release()

def postMessageIndividualNodes(ip_addresses, coap_path, message, port=5683, timeout=1,  no_response=True):

    # define how many threads can be active at any given time
    active_threads_sem = threading.Semaphore(5)

    # define variable to hold all the thread defines
    threads = []

    print(" COAP SERVER: posting messages to : " + str(ip_addresses) + " " + str(type(ip_addresses)))

    # message all nodes in ip_addresses
    for addr in ip_addresses:

        # create thread and append it to thread list
        threads.append(threading.Thread(target=postMessageNodeThread,
                                        args=(active_threads_sem, addr, coap_path, message, port, timeout, no_response,)))
        # start thread
        threads[-1].start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

def getMessageIndividualNodes(ip_addresses, coap_path, message=str(), port=5683, timeout=1,  no_response=True):

    # define how many threads can be active at any given time
    active_threads_sem = threading.Semaphore(5)

    # define variable to hold all the thread defines
    threads = []

    print(" COAP SERVER: GET request to : " + str(ip_addresses) + " " + str(type(ip_addresses)))

    # message all nodes in ip_addresses
    for addr in ip_addresses:

        # create thread and append it to thread list
        threads.append(threading.Thread(target=getMessageNodeThread,
                                        args=(active_threads_sem, addr, coap_path, port, timeout, no_response,)))
        # start thread
        threads[-1].start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

# this function grabs a sensor data packet received from the glasses and sends it to a connected client
def sensorDataReceived(ip_data_queue, data_queue, addr_queue, port, data_collector_sem):

    # todo: this is only initialized once but will break if client changes IP and tries to reconnect

    # get ip address (dont start if no ip address given)
    ip_address_of_collector = ip_data_queue.get()
    # ip_address_of_collector = "fd11:1111:1122:ff:fe00:4000"
    # ip_address_of_collector = ip_data

    print("  COAP Server : will be sending data to : " + ip_address_of_collector + ":" + str(port))

    while(True):

        try:
            # grab data packet if available
            sender_addr, packet = data_queue.get(timeout=10)
            print(" DEBUG: grabbed from queue")
            # check if IP is in list of known (if not, add)
            addr_queue.put((sender_addr, 0))

            # todo: can make this more efficient by leaving socket open and making this a thread
            # define socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # connect to data collector
            s.connect((ip_address_of_collector, port))

            # encrypt message to be sent
            encrypted_packet = en.do_encrypt(packet)
            print("sending encrypted packet to : " + str(ip_address_of_collector) + " : " + str(port))
            # if this is a message to set leds
            # s.send(bytearray(message, 'utf-8'))
            s.send(encrypted_packet)

            if data_collector_sem.acquire(blocking=False):
                print("  COAP Server : closing data export thread")
                break
        except queue.Empty:

            # check if new IP has been given
            try:
                ip_address_of_collector = ip_data_queue.get(False)
            except queue.Empty:
                continue

            # check if socket is defined
            try:
                s
            except NameError:
                if data_collector_sem.acquire(blocking=False):
                    print("  COAP Server : closing data export thread")
                    break
                continue

            else:
                # close socket if exists
                s.close()

                if data_collector_sem.acquire(blocking=False):
                    print("  COAP Server : closing data export thread")
                    break
                continue

        finally:
            s.close()

class CaptivatesLoggerResource(Resource):
    def __init__(self, data_queue, name="CaptivatesLoggerResource", coap_server=None):
            super(CaptivatesLoggerResource, self).__init__(name, coap_server, visible=True,
                                                observable=True, allow_children=False)
            self.resource_type = "CaptivatesLoggerResource"
            self.content_type = "application/json"

            self.data_queue = data_queue

            # self.light1 = 0
            # self.light2 = 0
            #
            # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
            #               {"n": "light2", "v": self.light2, "u": "lx"}]
            # self.period = 5
            # self.read_sensor(True)

    def render_GET(self, request):
        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def render_PUT(self, request):
        self.edit_resource(request)

        # print("  COAP Server : Received Data Packet From : " + str(request.source[0]))

        # # grab unix time
        # epoch = long(time.time())

        # address of requester
        addr = str(request.source[0])
        # print("PUT")
        # print(len(request.payload))
        # print(str(request.payload))
        # push incoming packet into queue for handling
        self.data_queue.put([addr, request.payload])


        return self

    # def read_sensor(self, first=False):
    #     self.light1 = random.randint(0, 1000)
    #     self.light2 = random.randint(0, 2000)
    #     self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
    #                   {"n": "light2", "v": self.light2, "u": "lx"}]
    #     self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
    #     if not self._coap_server.stopped.isSet():
    #
    #         timer = threading.Timer(self.period, self.read_sensor)
    #         timer.setDaemon(True)
    #         timer.start()
    #
    #         if not first and self._coap_server is not None:
    #             self._coap_server.notify(self)
    #             self.observe_count += 1

class TimeSyncResource(Resource):
    def __init__(self, name="TimeSyncResource", import_ip_queue=None, coap_server=None):
        super(TimeSyncResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "TimeSyncResource"
        self.content_type = "application/octet-stream"

        self.ip_importer = import_ip_queue
        # self.light1 = 0
        # self.light2 = 0
        #
        # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # self.period = 5
        #self.read_sensor(True)

    def render_GET(self, request):
        # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        #               {"n": "light2", "v": self.light2, "u": "lx"}]
        #
        # self.payload = (defines.Content_types["application/json"], json.dumps(self.value))

        self.edit_resource(request)

        print("  COAP Server : BORDER ADDRESS REQUESTED BY: " + str(request.source[0]))

        # grab unix time
        epoch = int(time.time())

        # packet border IP address and system time
        # message = pack('50s2xq4x', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), epoch)
        message = syncMessage(epoch)
        # self.payload = (defines.Content_types["applicaiton/json"], str(message))

        # # address of requester
        addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes([addr], "borderTime", message)

        self.payload = message

        print("received GET on sync by : " + addr)

        return self

    def render_PUT(self, request):
        self.edit_resource(request)
        print("  COAP Server : NODE SENT IP TO BORDER : " + str(request.source[0]))
        # print("     IP: " + str(request.source[0]))
        # print("     Payload: " + str(request.payload))
        node_type, description, UID = unpack('12s12s8s', request.payload)
        # UID = int.fromt_bytes(UID, byteorder='little')
        # print("     UID: " + str(UID))
        self.ip_importer.put([str(request.source[0]), node_type.decode().rstrip('\x00'), description.decode().rstrip('\x00'), UID])

        # # grab unix time
        # epoch = long(time.time())
        #
        # # packet border IP address and system time
        # message = pack('50sl', str(ni.ifaddresses('wpan0')[10][1]['addr']), epoch)
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes(addr, "borderTime", message)

        return self

    # def read_sensor(self, first=False):
    #     self.light1 = random.randint(0, 1000)
    #     self.light2 = random.randint(0, 2000)
    #     self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
    #                   {"n": "light2", "v": self.light2, "u": "lx"}]
    #     self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
    #     if not self._coap_server.stopped.isSet():
    #
    #         timer = threading.Timer(self.period, self.read_sensor)
    #         timer.setDaemon(True)
    #         timer.start()
    #
    #         if not first and self._coap_server is not None:
    #             self._coap_server.notify(self)
    #             self.observe_count += 1

class NodeInfoResource(Resource):
    def __init__(self, name="TimeSyncResource", import_ip_queue=None, coap_server=None):
        super(NodeInfoResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "TimeSyncResource"
        self.content_type = "application/octet-stream"

        self.ip_importer = import_ip_queue

        self.node_type = "border".encode('utf-8')
        self.description = "border_1".encode('utf-8')
        self.UID = 1
        # self.light1 = 0
        # self.light2 = 0
        #
        # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # self.period = 5
        #self.read_sensor(True)

    def render_GET(self, request):
        # # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        # #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # #
        # # self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        #
        # self.edit_resource(request)
        #
        # print("  COAP Server : BORDER ADDRESS REQUESTED BY: " + str(request.source[0]))
        #
        # # grab unix time
        # epoch = int(time.time())
        #
        # # packet border IP address and system time
        # # message = pack('50s2xq4x', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), epoch)
        # message = syncMessage(epoch)
        # # self.payload = (defines.Content_types["applicaiton/json"], str(message))
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes([addr], "borderTime", message)
        # self.payload = (defines.Content_types["application/octet-stream", pack('12s12sq', self.node_type, self.description, self.UID))
        self.payload = pack('12s12sq', self.node_type, self.description, self.UID)

        print("received get request")

        return self

    def render_PUT(self, request):
        self.edit_resource(request)
        print("  COAP Server : NODE SENT IP TO BORDER : " + str(request.source[0]))
        # print("     IP: " + str(request.source[0]))
        # print("     Payload: " + str(request.payload))
        node_type, description, UID = unpack('12s12sq', request.payload)
        # print("     UID: " + str(UID))
        self.ip_importer.put([str(request.source[0]), node_type.decode().rstrip('\x00'), description.decode().rstrip('\x00'), UID])

        #
        # # grab unix time
        # epoch = long(time.time())
        #
        # # packet border IP address and system time
        # message = pack('50sl', str(ni.ifaddresses('wpan0')[10][1]['addr']), epoch)
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes(addr, "borderTime", message)

        return self

    # def read_sensor(self, first=False):
    #     self.light1 = random.randint(0, 1000)
    #     self.light2 = random.randint(0, 2000)
    #     self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
    #                   {"n": "light2", "v": self.light2, "u": "lx"}]
    #     self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
    #     if not self._coap_server.stopped.isSet():
    #
    #         timer = threading.Timer(self.period, self.read_sensor)
    #         timer.setDaemon(True)
    #         timer.start()
    #
    #         if not first and self._coap_server is not None:
    #             self._coap_server.notify(self)
    #             self.observe_count += 1

class LocationResource(Resource):
    def __init__(self, name="TimeSyncResource", import_ip_queue=None, coap_server=None):
        super(LocationResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "TimeSyncResource"
        self.content_type = "text/plain"

        self.ip_importer = import_ip_queue

        self.loc_msg_sizes = {'pos_x': 'f',
                              'pos_y': 'f',
                              'pos_z': 'f',
                              'pos_accuracy': 'f',
                              'tick_ms_pos': 'I',
                              'pos_epoch': 'I'}

        self.loc_labels_to_string = ""

        index = 0
        for key, val_ in self.loc_msg_sizes.items():
            self.loc_labels_to_string = self.loc_labels_to_string + key

            if (index < (len(self.loc_msg_sizes) - 1)):
                self.loc_labels_to_string = self.loc_labels_to_string + " "
            index += 1

        self.loc_total_header_types = ""
        for _, val in self.loc_msg_sizes.items():
            self.loc_total_header_types = self.loc_total_header_types + val


        self.msg_unpacked = namedtuple('msg_unpacked', self.loc_labels_to_string)

        self.light_room_client = init_client("lights.media.mit.edu", 10002)

        self.last_message_time = time.time()

        self.restart_light_room_tracker = 0

        # self.light1 = 0
        # self.light2 = 0
        #
        # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # self.period = 5
        #self.read_sensor(True)

    def render_GET(self, request):
        # # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        # #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # #
        # # self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        #
        # self.edit_resource(request)
        #
        # print("  COAP Server : BORDER ADDRESS REQUESTED BY: " + str(request.source[0]))
        #
        # # grab unix time
        # epoch = int(time.time())
        #
        # # packet border IP address and system time
        # # message = pack('50s2xq4x', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), epoch)
        # message = syncMessage(epoch)
        # # self.payload = (defines.Content_types["applicaiton/json"], str(message))
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes([addr], "borderTime", message)
        # self.payload = (defines.Content_types["application/octet-stream", pack('12s12sq', self.node_type, self.description, self.UID))
        # self.payload = pack('12s12sq', self.node_type, self.description, self.UID)

        return self

    def render_PUT(self, request):
        print("LOCATION PUT")

        self.edit_resource(request)

        self.msg_unpacked = namedtuple('msg_unpacked', self.loc_labels_to_string)
        self.msg_unpacked = (self.msg_unpacked._make(unpack(self.loc_total_header_types, request.payload)))._asdict()

        print(self.msg_unpacked)

        set_lights_active(self.light_room_client)
        update_fixtures_client(np.array([self.msg_unpacked['pos_x'], self.msg_unpacked['pos_z']]), self.light_room_client)

        self.last_message_time = time.time()
        self.restart_light_room_tracker = 1

        # print("  COAP Server : NODE SENT IP TO BORDER : " + str(request.source[0]))
        # print("     IP: " + str(request.source[0]))
        # print("     Payload: " + str(request.payload))
        # node_type, description, UID = unpack('12s12sq', request.payload)
        # print("     UID: " + str(UID))
        # self.ip_importer.put([str(request.source[0]), node_type.decode().rstrip('\x00'), description.decode().rstrip('\x00'), UID])

        #
        # # grab unix time
        # epoch = long(time.time())
        #
        # # packet border IP address and system time
        # message = pack('50sl', str(ni.ifaddresses('wpan0')[10][1]['addr']), epoch)
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes(addr, "borderTime", message)

        return self

    def last_PUT_time(self):

        return self.last_message_time

    def restart_light_room(self):
        if(self.restart_light_room_tracker):
            print("  COAP Server : Restarting Lighting Lab")
            set_lights_inactive(self.light_room_client)
            self.restart_light_room_tracker = 0


    # def read_sensor(self, first=False):
    #     self.light1 = random.randint(0, 1000)
    #     self.light2 = random.randint(0, 2000)
    #     self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
    #                   {"n": "light2", "v": self.light2, "u": "lx"}]
    #     self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
    #     if not self._coap_server.stopped.isSet():
    #
    #         timer = threading.Timer(self.period, self.read_sensor)
    #         timer.setDaemon(True)
    #         timer.start()
    #
    #         if not first and self._coap_server is not None:
    #             self._coap_server.notify(self)
    #             self.observe_count += 1

class TouchResource(Resource):
    def __init__(self, name="TimeSyncResource", import_ip_queue=None, coap_server=None):
        super(TouchResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "TimeSyncResource"
        self.content_type = "text/plain"

        self.ip_importer = import_ip_queue

        self.node_type = "border"
        self.description = "border_1"
        self.UID = 1
        # self.light1 = 0
        # self.light2 = 0
        #
        # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # self.period = 5
        #self.read_sensor(True)

    def render_GET(self, request):
        # # self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
        # #               {"n": "light2", "v": self.light2, "u": "lx"}]
        # #
        # # self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        #
        # self.edit_resource(request)
        #
        # print("  COAP Server : BORDER ADDRESS REQUESTED BY: " + str(request.source[0]))
        #
        # # grab unix time
        # epoch = int(time.time())
        #
        # # packet border IP address and system time
        # # message = pack('50s2xq4x', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), epoch)
        # message = syncMessage(epoch)
        # # self.payload = (defines.Content_types["applicaiton/json"], str(message))
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes([addr], "borderTime", message)
        # self.payload = (defines.Content_types["application/octet-stream", pack('12s12sq', self.node_type, self.description, self.UID))
        # self.payload = pack('12s12sq', self.node_type, self.description, self.UID)

        return self

    def render_PUT(self, request):
        print("TOUCH PUT")

        self.edit_resource(request)
        # print("  COAP Server : NODE SENT IP TO BORDER : " + str(request.source[0]))
        # print("     IP: " + str(request.source[0]))
        # print("     Payload: " + str(request.payload))
        # node_type, description, UID = unpack('12s12sq', request.payload)
        # print("     UID: " + str(UID))
        # self.ip_importer.put([str(request.source[0]), node_type.decode().rstrip('\x00'), description.decode().rstrip('\x00'), UID])

        #
        # # grab unix time
        # epoch = long(time.time())
        #
        # # packet border IP address and system time
        # message = pack('50sl', str(ni.ifaddresses('wpan0')[10][1]['addr']), epoch)
        #
        # # address of requester
        # addr = str(request.source[0])
        #
        # # post message to requester
        # postMessageIndividualNodes(addr, "borderTime", message)

        return self

    # def read_sensor(self, first=False):
    #     self.light1 = random.randint(0, 1000)
    #     self.light2 = random.randint(0, 2000)
    #     self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
    #                   {"n": "light2", "v": self.light2, "u": "lx"}]
    #     self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
    #     if not self._coap_server.stopped.isSet():
    #
    #         timer = threading.Timer(self.period, self.read_sensor)
    #         timer.setDaemon(True)
    #         timer.start()
    #
    #         if not first and self._coap_server is not None:
    #             self._coap_server.notify(self)
    #             self.observe_count += 1
# thread fuction
def msgReceiveThread(c, ip_data_queue, pass_ip_table_sem):

    global networkList

    # global captivate_labels_to_string
    prev_message = ""

    while True:

        # data received from client
        try:
            encrypted_data = c.recv(1024)
            if not encrypted_data:
                print('Bye')

                # lock released on exit
                # print_lock.release()
                break

            data = en.do_decrypt(encrypted_data)

            # print('prev_message : ' + str(prev_message) + "\t\t" + "current_message : " + str(data))
            if prev_message == 'set_led':
                msg_unpacked = ""
                prev_message = msg_unpacked

                print("  COAP Server : setting leds")
                # todo: this is multicast.....
                postMessageIndividualNodes(["FF03::1"], "lightC", data, timeout=TIMEOUT_ON_MSG)
                print(" DEBUG : set_led : " + str(data))
                # send payload to glasses
                # todo: how to pick ip address (is it the visualizer??)
                # postMessageIndividualNodes(ip_addresses, "lightC", data, port=5683)
                continue

            elif prev_message == 'set_data_ip':
                msg_unpacked = data.decode("utf-8")
                prev_message = msg_unpacked

                print("  COAP Server : setting ip to send data to : " + str(msg_unpacked))
                ip_data_queue.put(msg_unpacked)

            elif prev_message == "start_stream":

                # todo: how to pick ip address (is it the visualizer??)
                msg_unpacked = ""
                prev_message = msg_unpacked

                print("  COAP Server : starting stream on : " + str(msg_unpacked))

                postMessageIndividualNodes(["FF03::1"], "togLog", data, port=5683, timeout=TIMEOUT_ON_MSG)

            elif prev_message == "tare_system":

                # todo: how to pick ip address (is it the visualizer??)
                msg_unpacked = ""
                prev_message = msg_unpacked

                print("  COAP Server : starting stream on : " + str(msg_unpacked))

                postMessageIndividualNodes(["FF03::1"], "togLog", data, port=5683, timeout=TIMEOUT_ON_MSG)

            else:
                msg_unpacked = data.decode("utf-8")
                prev_message = msg_unpacked

                # if msg_unpacked == "start_stream":
                #     # todo: how to pick ip address (is it the visualizer??)
                #     data = pack('BBBBBB', 1, 1, 1, 1, 1, 1)
                #     postMessageIndividualNodes(["FF03::1"], "togLog", data, port=5683, timeout=TIMEOUT_ON_MSG)
                #     # postMessageIndividualNodes(ip_addresses, "togLog", data, port=5683)
                #     continue
                if msg_unpacked == "get_ip_table":
                    print("  COAP Server : sending IP table to connected client")
                    print(networkList)
                    # convert dictionary to string, encrypt it, and send
                    encrypted_msg = en.do_encrypt(json.dumps(networkList))
                    c.send(encrypted_msg)

                elif msg_unpacked == "stop_stream":
                    # todo: how to pick ip address (is it the visualizer??)
                    data = pack('BBBBBB', 0, 0, 0, 0, 0, 0)
                    postMessageIndividualNodes(["FF03::1"], "togLog", data, port=5683, timeout=TIMEOUT_ON_MSG)
                    # postMessageIndividualNodes(ip_addresses, "togLog", data, port=5683)
                    continue
                elif msg_unpacked == "broadcast_border_ip":

                    # reset IP table
                    networkList = {}

                    # grab unix time
                    epoch = int(time.time())

                    # packet border IP address and system time
                    message = syncMessage(epoch, send_IP=1)
                    # message = pack('50sq', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), epoch)
                    # self.payload = (defines.Content_types["applicaiton/json"], str(message))
                    # print(" DEBUG : broadcast_border_ip : " + str(message))
                    # post message to requester

                    # multicast border IP and server Time
                    postMessageIndividualNodes(["FF03::1"], "borderTime", message, timeout=TIMEOUT_ON_MSG)

                    # multicast a get request for node information
                    getMessageIndividualNodes(["FF03::1"], "nodeInfo", timeout=TIMEOUT_ON_MSG)

            # print('af -> prev_message : ' + str(prev_message) + "\t\t" + "current_message : " + str(data))



        except KeyboardInterrupt:
            break

        # # reverse the given string from client
        # data = data[::-1]
        #
        # # send back reversed string to client
        # c.send(data)

        # connection closed
    c.close()

#
# def msgParser(msg_queue, msgParserSem):
#     while True:
#         try:
#             if msgParserSem.acquire(blocking=False):
#                 break
#             msg_unpacked = msg_queue.get(timeout=1000)
#             print(msg_unpacked)
#             # capData.add_data(msg_unpacked)
#         #
#         # except KeyboardInterrupt:
#         #     break
#
#         except queue.Empty:
#             continue

class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)
        print(("  COAP Server : start on " + host + ":" + str(port)))

def systemControlThread(host, port_data, data_control_sem, ip_data_queue, pass_addr_table_sem):
    #
    # # start queue for message passing between threads
    # msg_queue = multiprocessing.Queue()

    # bind socket to start server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    s.bind((host, port_data))

    # put the socket into listening mode
    print("  COAP Server : Listening for commands on : " + host + ":" + str(port_data))
    s.listen(5)


    while True:
        try:
            # establish connection with client
            c, addr = s.accept()

            # lock acquired by client
            #print_lock.acquire()
            print('  COAP Server : Connected to :', addr[0], ':', addr[1])

            # Start a new thread and return its identifier
            start_new_thread(msgReceiveThread, (c, ip_data_queue, pass_addr_table_sem, ))

            # break thread if told to do so
            if data_control_sem.acquire(blocking=False):
                break
        except KeyboardInterrupt:

            print('  COAP Server : INTERRUPT RECEIVED')

            # break thread if told to do so
            if data_control_sem.acquire(blocking=False):
                break

            #
            #
            # print('  CAPTIVATE LOGGER : WAIT FOR THREADS TO FINISH!')
            # msgParserSem.release()
            # time.sleep(2)
            # parser.join()
            break

        except socket.timeout as e:
            if data_control_sem.acquire(blocking=False):
                break

    print("  COAP Server : closing data control thread")

    # print("  COAP Server : NOTIFYING NODES TO START STREAMING")
    #
    # # grab unix time
    # epoch = long(time.time())
    #
    # # packet border IP address and system time
    # message = pack('50sl', str(ni.ifaddresses('wpan0')[10][1]['addr']), epoch)
    # # self.payload = (defines.Content_types["applicaiton/json"], str(message))
    #
    # # address of requester
    # addr = str(request.source[0])
    #
    # # post message to requester
    # postMessageIndividualNodes(addr, "borderTime", message)


IP_STALE_THRESHOLD = 60 # in seconds
IP_BROADCAST_MULTICAST_PERIOD = 30  # in seconds
IP_STALE_CHECK_PERIOD = 30  # in seconds

# function to periodically multicast IP of border router to all nodes
#  todo: rewrite coap code to allow for multicast receiving (10/4: currently can only transmit multicast)
def broadcastAddressToNodes():

    # grab unix time
    epoch = int(time.time())

    # packet border IP address and system time
    message = syncMessage(epoch)
    # message = pack('50s2xq4x', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), epoch)
    # self.payload = (defines.Content_types["applicaiton/json"], str(message))

    # post message to requester
    postMessageIndividualNodes(["FF03::1"], "borderTime", message)

    # time.sleep(2)

    # delete any IPs that have gone stale in IP table
    # staleAddressCheck()


# function to check if IP address in table is stale (e.g. has dropped from network)
def staleAddressCheck():
    global networkList, IP_STALE_THRESHOLD

    currentTime = int(time.time())

    # key : unique_identifier
    # value : [ identifiger , ip_address , epoch ]
    #               identifier  = i.e. "captivates"
    #               ip_address  = ipv6 address
    #               epoch       = 32-bit integer for when IP address was received

    # run through IP table and check if any IPs have gone stale
    message = pack('50sl', str(ni.ifaddresses('wpan0')[10][0]['addr']).encode(), currentTime)
    expired_IPs = []
    for key, value in networkList.items():
        if abs(currentTime - value[2]) < IP_STALE_THRESHOLD:
            expired_IPs.append(key)

    # try to unicast stale nodes and if that doesn't work, remove them from IP table
    if len(expired_IPs) is not 0:
        postMessageIndividualNodes(expired_IPs, "devInfo", message)

def checkLightingLabTimeout(location_resource):
    if( (time.time() - location_resource.last_PUT_time()) > LIGHTS_TIMEOUT_TIME):
        location_resource.restart_light_room()

    threading.Timer(LIGHTS_TIMEOUT_TIME, checkLightingLabTimeout, args=[location_resource]).start()

def coapServer():
    global IP_BROADCAST_MULTICAST_PERIOD, IP_STALE_CHECK_PERIOD, IP_STALE_THRESHOLD
    # IP address and port of server
    # ip = "0.0.0.0"
    try:
        ip = str(ni.ifaddresses('wpan0')[10][0]['addr'])
    except IndexError:
        print("  COAP Server : ERROR : No \"wpan0\" IP detected!")
        print("  COAP Server : are you running OpenThread border router?")
        return
    port = 5683

    # can server do multicast
    # todo: unsure what this flag does since there is a lack in the documentation explaining it
    multicast = False

    # ports for data comms
    port_control = 5554  # port for passing control messages to COAP server
    port_data = 5555  # port for passing data from COAP to server (i.e. data aggregator)

    # queue for putting received individual IP addresses in
    recv_addr_queue = multiprocessing.Queue()

    # queue for data collection
    data_queue = multiprocessing.Queue()

    # queue for exporting IP address table
    addr_export_queue = multiprocessing.Queue()

    # semaphore to tell thread to add the latest table to queue
    pass_addr_table_sem = threading.Semaphore()
    pass_addr_table_sem.acquire()

    # semaphore to that triggers address table reset
    reset_addr_table_sem = threading.Semaphore()
    reset_addr_table_sem.acquire()

    # define coap server
    print("  COAP Server : IP : " + str(ip))
    server = CoAPServer(host=ip, port=port, multicast=multicast)

    # define and add resources
    logger = CaptivatesLoggerResource(data_queue=data_queue, coap_server=server)
    time_sync = TimeSyncResource(coap_server=server, import_ip_queue=recv_addr_queue)
    node_info = NodeInfoResource(coap_server=server, import_ip_queue=recv_addr_queue)
    test_resource = DebugResource(coap_server=server)
    touch_resource = TouchResource(coap_server=server)
    location_resource = LocationResource(coap_server=server)

    server.add_resource('nodeInfo/', node_info)
    server.add_resource('borderLog/', logger)
    server.add_resource('borderTime/', time_sync)
    server.add_resource('borderTest/', test_resource)
    server.add_resource('capTouch/', touch_resource)
    server.add_resource('capLoc/', location_resource)

    '''
    THREADS
    '''
    # start thread to check for command data from data logging python code
    ip_control = str(ni.ifaddresses('eth0')[2][0]['addr'])  # control IP is public IPv4
    data_control_sem = threading.Semaphore()
    data_control_sem.acquire()
    system_control_thread = threading.Thread(target=networkAddrHandler,
                                             args=(recv_addr_queue, addr_export_queue, reset_addr_table_sem , pass_addr_table_sem, ))
    system_control_thread.setDaemon(True)
    system_control_thread.start()

    # start data collection handler thread that passes data via socket to data collector
    #    todo: figure out where to properly send data
    # ip_data = "18.27.117.133"
    # todo: in control scheme, allow for IP to be sent via system_control_thread
    # ip_data = "18.20.174.0"
    ip_data_queue = multiprocessing.Queue()
    data_collector_sem = threading.Semaphore()
    data_collector_sem.acquire()
    data_collector_thread = threading.Thread(target=sensorDataReceived,
                                    args=(ip_data_queue, data_queue, recv_addr_queue, port_data, data_collector_sem,))
    data_collector_thread.setDaemon(True)
    data_collector_thread.start()

    # start thread to check for command data from data logging python code
    ip_control = str(ni.ifaddresses('eth0')[2][0]['addr'])  # control IP is public IPv4
    data_control_sem = threading.Semaphore()
    data_control_sem.acquire()
    system_control_thread = threading.Thread(target=systemControlThread,
                                    args=(ip_control, port_control,data_control_sem, ip_data_queue, pass_addr_table_sem,))
    system_control_thread.setDaemon(True)
    system_control_thread.start()



    '''
    TIMERS
    '''
    lightingLabTimer = threading.Timer(LIGHTS_TIMEOUT_TIME, checkLightingLabTimeout, args=[location_resource])
    lightingLabTimer.start()

    # broadcastAddr = threading.Timer(IP_BROADCAST_MULTICAST_PERIOD, broadcastAddressToNodes)
    # broadcastAddr.start()

    # broadcast border router to all nodes and grab IPs of all nodes in network
    broadcastAddressToNodes()

    # start coap server
    print("  COAP Server : Starting Server on : " + ip + ":" + str(port))
    try:
        server.listen(10)

    # error checking
    except KeyboardInterrupt:
        print("  COAP Server : Restarting Lighting Lab")
        location_resource.restart_light_room()

        print("  COAP Server : Shutdown")
        server.close()

        print("  COAP Server : Closing Threads")
        data_control_sem.release()
        data_collector_sem.release()

        # time.sleep(2)

        system_control_thread.join()
        data_collector_thread.join()

        print("  COAP Server : Exiting...")

#defines.ALL_COAP_NODES_IPV6

if __name__ == "__main__":
    coapServer()



