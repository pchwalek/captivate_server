# from direct.directbase import DirectStart
# from panda3d.ode import OdeWorld, OdeBody, OdeMass

import numpy as np
import serial
import struct
import threading
from multiprocessing import Queue
import queue
import time
import socket

import colorsys
from lights_controller import *

# ser = serial.Serial(
#     port='COM5',\
#     baudrate=9600,\
#     parity=serial.PARITY_NONE,\
#     stopbits=serial.STOPBITS_ONE,\
#     bytesize=serial.EIGHTBITS,\
#         timeout=None)

# print("connected to: " + ser.portstr)

#Wait for start message before reading print statements

# while True:
#     line = ser.readline()
#     if(line[-6:].decode() == "start\n"):
#         print("started")
#         break;

# bs_0_xyz = ser.read(12)
# bs_0_x, bs_0_y, bs_0_z = struct.unpack(3 * 'f', bs_0_xyz)
# base_station_0.setPos(100 * bs_0_x, 100 * -bs_0_z, 100 * bs_0_y/2)
# base_station_0.setScale(1, 100 * bs_0_y/2, 1)
#
# bs_1_xyz = ser.read(12)
# bs_1_x, bs_1_y, bs_1_z = struct.unpack(3 * 'f', bs_1_xyz)
# base_station_1.setPos(100 * bs_1_x, 100 * -bs_1_z, 100 * bs_1_y/2)
# base_station_1.setScale(1, 100 * bs_1_y/2, 1)
# print("Base station coords")
# print(bs_0_x, bs_0_y, bs_0_z)
# print(bs_1_x, bs_1_y, bs_1_z)

port_loc_vis    = 5556 # port for passing data to visualizer
from struct import *




# fixture_positions = np.array([[1.5, -3.0],
#                               [1.5, -2.8],
#                               [1.5, -2.5],
#                               [1.4, -2.1],
#                               [1.37, -0.8],
#                               [1.35, -00.4],
#
#                               [-0.5, -2.3],
#                               [-0.5, -2.1],
#                               [-0.5, -1.4],
#                               [-0.5, -1.2],
#                               [-0.5, -0.5],
#                               [-0.5, -0.25],
#
#                               [0.68, -1.9],
#                               [1, -2.25],
#                               [1.23, -2.44],
#                               [1.35, -2.23],
#
#                               [-0.07, -1.27],
#                               [0.027, -1.15],
#                               [0.21, -1.14],
#                               [0.48, -1.3]])

fixture_positions = np.array([[1.3114,	1.4955,	0.8721],
                              [1.1021,	1.4719,	0.9067],
                              [0.4210,	1.4004,	0.8931],
                              [0.1319,	1.3752,	0.8489],
                              [-0.6311,	1.3238,	0.8202],
                              [-0.9208,	1.3077,	0.8020],

                              [1.3114,	1.4955, -0.9245],
                              [1.1021,	1.4719,	-0.9245],
                              [0.4210,	1.4004,	-0.9245],
                              [0.1319,	1.3752,	-0.9245],
                              [-0.6311,	1.3238,	-0.9245],
                              [-0.9208,	1.3077,	-0.9245],

                              [0.7567, 1.0768, 0.3300],
                              [0.3887, 1.0642, 0.3300],
                            [0.0662, 1.0532, 0.3300],
                            [-0.3308, 1.0379, 0.3300],

                            [0.7567, 1.0768, -0.2400],
                            [0.3887, 1.0642, -0.2400],
                            [0.0662, 1.0532, -0.2400],
                            [-0.3308, 1.0379, -0.2400],

])


def update_fixtures(cur_pos):
    global lights_client

    dp = fixture_positions[:,[0,2]] - cur_pos
    distances = np.linalg.norm(dp, axis=1)
    intensity = (0.5 - np.clip(distances, 0.0, 0.5)) / 0.5

    for i in range(fixture_positions.shape[0]):
        set_color(client, i + 1, colorsys.hsv_to_rgb(0.5, 1.0, intensity[i]))


def update_fixtures_client(cur_pos, client):
    global lights_client

    dp = fixture_positions[:, [0, 2]] - cur_pos
    distances = np.linalg.norm(dp, axis=1)
    intensity = (0.5 - np.clip(distances, 0.0, 0.5)) / 0.5

    for i in range(fixture_positions.shape[0]):
        set_color(client, i + 1, colorsys.hsv_to_rgb(0.5, 1.0, intensity[i]))


def server_reader(queue):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', port_loc_vis))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    x, y, z = unpack("fff", data)

                    update_fixtures(np.array([x, z]))

                    queue.put([100*x, 100*(-z), 100*y, 0, 0])
                    # conn.sendall(data)

    # x = 0
    # y = 0
    # z = 0
    #
    # while True:
    #     x += 1
    #     y += 1
    #     z += 1
    #
    #     time.sleep(0.1)
    #     queue.put([x, y, z, 0, 0])
    #
    #     try:
    #         server.listen(10)
    #
    #     encrypted_data = c.recv(1024)
    #
    #     # error checking
    #     except KeyboardInterrupt:
    #         print("  COAP Server : Shutdown")
    #         server.close()



# def serial_reader(ser):
#     global x, y, z
#     while True:
#         line = ser.read(12)
#         #32 bit float
#         #y and z are flipped
#         x_s, y_s, z_s = struct.unpack(3 * 'f', line)
#         x, y, z = 100 * x_s, 100 * -z_s, 100 * y_s
#         print(x_s, y_s, z_s)
#     ser.close()
#




# The task for our simulation
# def simulationTask(task):
#     global deltaTimeAccumulator
#     # Add the deltaTime for the task to the accumulator
#     deltaTimeAccumulator += globalClock.getDt()
#     while deltaTimeAccumulator > stepSize:
#         # Remove a stepSize from the accumulator until
#         # the accumulated time is less than the stepsize
#         deltaTimeAccumulator -= stepSize
#     sphere.setPos(x, y, z)
#     return task.cont

# The task for our simulation
def simulationTask(task):
    global server_queue

    try:
        x, y, z, _, _ = server_queue.get_nowait()
        sphere.setPos(x, y, z)
    except queue.Empty:
        pass

    return task.cont
    # # Add the deltaTime for the task to the accumulator
    # deltaTimeAccumulator += globalClock.getDt()
    # while deltaTimeAccumulator > stepSize:
    #     # Remove a stepSize from the accumulator until
    #     # the accumulated time is less than the stepsize
    #     deltaTimeAccumulator -= stepSize
    # sphere.setPos(x, y, z)
    # return task.cont

if(__name__ == "__main__"):
    from panda3d.core import Quat, LineSegs, Mat4

    x = 0
    y = 0
    z = 0
    accuracy = 0
    time = 0

    server_queue = Queue()

    client = init_client("lights.media.mit.edu", 10002)
    set_lights_active(client)

    serial_thread = threading.Thread(target=server_reader, args=(server_queue,))
    serial_thread.start()

    # Create an accumulator to track the time since the sim
    # has been running
    deltaTimeAccumulator = 0.0
    # This stepSize makes the simulation run at 90 frames per second
    stepSize = 1.0 / 90.0

    x, y, z = (0, 0, 0)

    # Draw axes
    axes_segs = LineSegs("axes");
    # x axis
    axes_segs.setColor(217 / 255, 67 / 255, 56 / 255, 1)
    axes_segs.moveTo(-1000, 0, 0)
    axes_segs.drawTo(1000, 0, 0)

    # y axis
    axes_segs.setColor(56 / 255, 67 / 255, 217 / 255, 1)
    axes_segs.moveTo(0, -1000, 0)
    axes_segs.drawTo(0, 1000, 0)

    # z axis
    axes_segs.setColor(56 / 255, 217 / 255, 56 / 255, 1)
    axes_segs.moveTo(0, 0, -1000)
    axes_segs.drawTo(0, 0, 1000)
    segsnode = axes_segs.create(False);
    render.attachNewNode(segsnode);

    # Load the smiley model which will act as our iron ball
    sphere = loader.loadModel("smiley.egg")
    sphere.reparentTo(render)
    sphere.setPos(0, 0, 0)
    sphere.setColor(0.7, 0.4, 0.4)

    base_station_0 = loader.loadModel("cylinder.x")
    base_station_0.reparentTo(render)
    base_station_0.setHpr(0, 90, 0)
    base_station_0.setColor(0, 0, 0, 1)

    base_station_1 = loader.loadModel("cylinder.x")
    base_station_1.reparentTo(render)
    base_station_1.setHpr(0, 90, 0)
    base_station_1.setColor(0, 0, 0, 1)

    # b0 origin -2.104828 2.384802 -1.427797 matrix -0.496826 0.343897 -0.796805 0.008548 0.920031 0.391751 0.867808 0.187821 -0.460036
    # b1 origin 1.738303 2.430314 0.781285 matrix 0.285992 -0.253563 0.924075 0.040683 0.966697 0.252668 -0.957368 -0.034667 0.286784

    bs_0_x, bs_0_y, bs_0_z = [-2.104828, 2.384802, -1.427797]
    base_station_0.setPos(100 * bs_0_x, 100 * -bs_0_z, 100 * bs_0_y / 2)
    base_station_0.setScale(1, 100 * bs_0_y / 2, 1)

    bs_1_x, bs_1_y, bs_1_z = [1.738303, 2.430314, 0.781285]
    base_station_1.setPos(100 * bs_1_x, 100 * -bs_1_z, 100 * bs_1_y / 2)
    base_station_1.setScale(1, 100 * bs_1_y / 2, 1)

    mat = Mat4(camera.getMat())
    mat.invertInPlace()
    base.mouseInterfaceNode.setMat(mat)
    base.enableMouse()

    # base.camera.setPos(0, 0, 40)
    # base.camera.lookAt(0, 0, 0)
    base.trackball.node().setPos(0, 20, 0)

    taskMgr.doMethodLater(0.05, simulationTask, "VIVE Position Visualizer")

    try:
        base.run()
    except KeyboardInterrupt:
        client.send_message("/set_inactive", 1)



def run3D_visualizer(location_queue):
    global x, y, z

    while True:
        [x, y, z, _, _] = location_queue.get()
        print(str(x))

