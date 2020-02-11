import sys
import time
import socket
import select
from struct import *
import numpy as np


sys.path.append('/home/pi/captivate/dataViz/CoAPthon3')
from coapthon.client.helperclient import HelperClient

import time

# try:
print(" TRYING FF02::1")
client = HelperClient(server=("ff02::1", 5683))

color_array = (np.ones(18)*50).astype(int).tolist()

message = pack("18B", *color_array)
response = client.put("lightC", message, timeout=1, no_response=True)
# response = client.send_empty()
client.stop()
# except:
#     print(" FIRST ERROR")

#
# time.sleep(4)
#
# try:
#     print(" TRYING FF02::1%wpan0")
#     client = HelperClient(server=("ff02::1%wpan0", 5683))
#     response = client.put("lightS", "bleh", timeout=1, no_response=True)
#     # response = client.send_empty()
#     client.stop()
# except:
#     print(" SECOND ERROR")
#
# time.sleep(4)
#
# try:
#     print(" TRYING fd11:22:0:0:e089:5c58:89c7:38f9")
#     client = HelperClient(server=("fd11:22:0:0:e089:5c58:89c7:38f9", 5683))
#     response = client.put("lightS", "bleh", timeout=1, no_response=True)
#     # response = client.send_empty()
#     client.stop()
# except:
#     print(" THIRD ERROR")

