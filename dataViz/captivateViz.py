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

# import subprocess as subprocess
# subprocess.call('python C:/dev/glasses/dataViz/vive_pos_visualizer.py')

#from pylive.pylive import live_plotter

# DATA_SAVE_DIRECTORY = "C:/dev/flow/project_flow/data/"

# recording_save_path = "C:/dev/flow/project_flow/data/"


if __name__ == '__main__':
    # import sys
    # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #     QtGui.QApplication.instance().exec_()

    # t = QtCore.QTimer()
    # t.start(50)
    #QtGui.QApplication.instance().exec_()

    server_IP = "18.27.126.69"

    recording = 0
    test_number = 0
    # save_path = "C:/dev/flow/project_flow/data/" + "test_" + str(test_number) + "/"

    captivate_queue = multiprocessing.Queue()
    captivate_queue_alert = multiprocessing.Queue()

    daemon = False

    # ports for data comms
    port_control    = 5554 # port for passing control messages to COAP server
    port_data       = 5555 # port for passing data from COAP to server (i.e. data aggregator)
    port_loc_vis    = 5556 # port for passing data to visualizer

    # queues to update plots
    blink_queue = Queue()
    temp_queue = Queue()
    pos_queue = Queue()
    inertial_queue = Queue()
    loc_visualizer_queue = Queue()

    # semaphore to send to logging thread so to be able to turn it off
    system_semaphore = threading.Semaphore()
    system_semaphore.acquire()

    # thread declaration for data collector
    data_collector_thread = threading.Thread(target=runDataCollector, args=(system_semaphore, blink_queue, temp_queue, pos_queue, inertial_queue,))
    localization_viz_thread = threading.Thread(target=runDataCollector, args=(system_semaphore, blink_queue, temp_queue, pos_queue, inertial_queue,))

    # declare processes and ensure daemon is True to that processes exit when application is closed
    # of_process = multiprocessing.Process(target=of.runOpenFace, args=(openface_queue, openface_queue_alert,))
    # eeg_process = multiprocessing.Process(target=ob.runOpenBCI, args=(EEG_queue,EEG_queue_alert, ))
    # eda_process = multiprocessing.Process(target=eda.runEDA, args=(EDA_queue, EDA_queue_alert, ))
    # recording_process = multiprocessing.Process(target=rv.runVideoRecord, args=(save_path, recording_queue_alert,))

    if daemon == True:
        of_process.daemon = True
        eeg_process.daemon = True
        eda_process.daemon = True
        recording_process.daemon = True

    activityClasses = ['Unknown',
                       'In-Vehicle',
                       'On-Bicycle',
                       'On-Foot',
                       'Still',
                       'Tilting',
                       'Walking',
                       'Running',
                       'OnStairs']

    # # for live plotter
    # size = 300
    # line1 = []
    # x_vec = np.linspace(0, 1, size + 1)[0:-1]
    # y_vec = np.random.randn(len(x_vec))
    #
    # size = 100
    # line2 = []
    # x_vec_2 = np.linspace(0, 1, size + 1)[0:-1]
    # y_vec_2 = np.random.randn(len(x_vec_2))

    # instantiate graphic window for plots
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    area = DockArea()
    win.setCentralWidget(area)
    win.resize(2500, 1200)
    win.setWindowTitle('Captivate\'s Dashboard')

    #  *******************************************************************  #
    #  ***************** AREA DEFINES ************************************  #
    #  *******************************************************************  #


    def sendControlMessage(message, special_type=""):
        global port_control, system_semaphore

        # as a client, tell COAP server to tell glasses to start streaming
        # host = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connect to COAP server on local computer
        s.connect((server_IP, port_control))

        # if this is a message to set leds
        if special_type == "set_led":
            encrypted_msg = en.do_encrypt('set_led')

            # s.send(bytearray('set_led', 'utf-8'))
            s.send(encrypted_msg)

            # # crude way of resetting connection
            # s.close()
            # s.connect((host, port_control))


            time.sleep(.1)

            encrypted_msg = en.do_encrypt(message)
            s.send(encrypted_msg)

        elif special_type == "set_data_ip":
            encrypted_msg = en.do_encrypt('set_data_ip')

            # s.send(bytearray('set_led', 'utf-8'))
            s.send(encrypted_msg)

            # # crude way of resetting connection
            # s.close()
            # s.connect((host, port_control))


            time.sleep(.1)

            encrypted_msg = en.do_encrypt(message)
            s.send(encrypted_msg)

        elif special_type == "get_ip_table":
            encrypted_msg = en.do_encrypt('get_ip_table')

            # s.send(bytearray('set_led', 'utf-8'))
            s.sendall(encrypted_msg)

            # wait for response
            # Look for the response
            amount_received = 0
            amount_expected = 1024
            start_time = time.time()

            while True:
                data = s.recv(1024)
                amount_received += len(data)

                decrypted_data = en.do_decrypt(data)
                refresh_IP_table(json.loads(decrypted_data))

                break
                # # if waiting for longer than 2 seconds, break
                # if (time.time() - start_time) > 2:
                #     break
        # if this is any other command message

        else:
            encrypted_msg = en.do_encrypt(message)
            s.send(encrypted_msg)
            # s.send(bytearray(message, 'utf-8'))

        # close connection
        s.close()

    ## Create docks, place them into the window one at a time.
    ##   Note that size arguments are only a suggestion; docks will still have to
    ##   fill the entire dock area and obey the limits of their internal widgets.
    d1 = Dock("Control", size=(300, 75))  ## give this dock the minimum possible size
    # d2 = Dock("LED", size=(600, 500))  ## give this dock the minimum possible size

    # d2 = Dock("Dock2 - Console", size=(500, 300), closable=True)

    d_inertial = Dock("Inertial Data", size=(150, 75), closable=True)

    d_input_console = Dock("Server Functions", size=(150, 50), closable=True)

    d_ip_table = Dock("IP_Table", size=(100, 150), closable=True)

    # LED CONTROLS
    d_led_all = Dock("All LED", size=(350, 40), closable=True)
    d_led_set = Dock("LED Control", size=(75, 50))
    d_led_left_eye = Dock("Left Eye", size=(75, 50), closable=True)
    d_led_right_eye = Dock("Right Eye", size=(75, 50), closable=True)
    d_led_left_top = Dock("Left Top", size=(75, 50), closable=True)
    d_led_right_top = Dock("Right Top", size=(75, 50), closable=True)
    d_led_left_front = Dock("Left Front", size=(75, 50), closable=True)
    d_led_right_front = Dock("Right Front", size=(75, 50), closable=True)

    # d4 = Dock("Dock4 (tabbed) - Plot", size=(500, 200))
    plotWidth = 8000
    plotHeight = 150
    d_blink = Dock("Blink", size=(plotWidth, plotHeight), closable=True)
    d_nose_temp = Dock("Nose Temp", size=(plotWidth, plotHeight), closable=True)
    d_temple_temp = Dock("Temple Temp", size=(plotWidth, plotHeight), closable=True)
    d_diff_temp = Dock("Delta Temp (Nose - Temple)", size=(plotWidth, plotHeight), closable=True)
    # d9 = Dock("Eye Angle X", size=(800, 200), closable=True)
    # d10 = Dock("Eye Angle Y", size=(800, 200), closable=True)

    #  *******************************************************************  #
    #  ***************** PLACEMENT DEFINE ********************************  #
    #  *******************************************************************  #

    area.addDock(d1, 'left')  ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
    #area.addDock(d2, 'right')  ## place d2 at right edge of dock area
    area.addDock(d_inertial, 'bottom', d1)  ## place d3 at bottom edge of d1
    area.addDock(d_input_console, 'bottom', d_inertial)
    area.addDock(d_ip_table, 'right', d_inertial)


    area.addDock(d_led_all, 'bottom', d_input_console) ## eeg

    area.addDock(d_led_right_front, 'bottom', d_led_all)
    area.addDock(d_led_right_eye, 'left', d_led_right_front)
    area.addDock(d_led_right_top, 'left', d_led_right_eye)
    area.addDock(d_led_left_top, 'left', d_led_right_top)
    area.addDock(d_led_left_eye, 'left', d_led_left_top)
    area.addDock(d_led_left_front, 'left', d_led_left_eye)

    area.addDock(d_led_set, 'right', d_led_right_front)  ## place d3 at bottom edge of d1

    area.addDock(d_blink, 'right')
    area.addDock(d_nose_temp, 'bottom', d_blink)
    area.addDock(d_temple_temp, 'bottom', d_nose_temp)
    area.addDock(d_diff_temp, 'bottom', d_temple_temp)



    #  *******************************************************************  #
    #  ***************** IP ADDRESS WIDGET *******************************  #
    #  *******************************************************************  #

    class myListWidget(QListWidget):

        def Clicked(self, item):
            # print("clicked")
            QMessageBox.information(self, "ListWidget", "You clicked: " + item.text())

    w_layout = pg.LayoutWidget()

    label_server_ip = QtGui.QLabel(""" -- Server Settings -- 
            """)



    # w_layout.resize(600, 200)
    ip_textBox = QLineEdit(server_IP)
    # ip_textBox.move(250, 120)

    ip_button = QPushButton("SET SERVER IP")

    ip_border_sync_nodes_button = QPushButton("FORCE BORDER MULTICAST SYNC")

    ip_border_get_ip_tables_button = QPushButton("FORCE UPDATE IP TABLES")

    # ip_button.setStyleSheet("QPushButton { background-color: green }"
    #                       "QPushButton:pressed { background-color: blue }")
    # ip_button.move(20, 80)

    # ip_list = myListWidget()

    ip_list = pg.TreeWidget()
    ip_list.setWindowTitle('ip_table')
    # ip_list.setColumnCount(2)
    ip_list.headerItem().setText(1, "Node IPs")
    ip_list.headerItem().setText(0, "UID")
    # ip_list.header().setVisible(False)

    # ip_list = pg.QtGui.QTextList([])
    # ip_list = QView

    d_input_console.addWidget(label_server_ip, 0, 0)
    d_input_console.addWidget(ip_textBox, 1, 0)
    d_input_console.addWidget(ip_button, 2, 0)
    d_input_console.addWidget(ip_border_sync_nodes_button, 3, 0)
    d_input_console.addWidget(ip_border_get_ip_tables_button, 4, 0)
    # d_input_console.addWidget(ip_list, 0, 1)
    d_ip_table.addWidget(ip_list, 0, 0)
    # w_line_edit = QLineEdit()

    ip_table = ["tot", "totd", "tdjs"]

    # for item in ip_list:
    # list_item = QListWidgetItem(item)
    # ip_list.append(list_item)
    # node_ips = QtGui.QTreeWidgetItem(["node_ips"])
    # ip_list.addTopLevelItem(node_ips)

    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[0]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[1]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[2]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[0]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[1]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[2]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[0]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[1]]))
    # node_ips.addChild(QtGui.QTreeWidgetItem([ip_table[2]]))
    ip_list.expandAll()

    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem(["test", "test"]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[1]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[2]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[0]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[1]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[2]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[0]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[1]]))
    # ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([ip_table[2]]))

    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, int)
    def test_function(it, col):
        global ip_list

        print("  selected IP : " + str(it.text(col)))
        #
        # print(it, col, it.text(col))
        # print(ip_list.headerItem)

        # print("CLICKED")

    # button_item = QtGui.QPushButton('Button')
    # button_item.clicked.connect(test_function)
    # test = pg.TreeWidgetItem(['test'])
    # test.setWidget(1, button_item)

    # ip_list.addTopLevelItem(test)

    ip_list.itemClicked.connect(test_function)

    def refresh_IP_table(data):
        print("  CapViz : refreshing ip tables")
        global ip_list
        ip_list.clear()
        for item in data.keys():
            ip_list.addTopLevelItem(QtGui.QTreeWidgetItem([str(0),str(item)]))

    def connectToServer():
        global ip_textBox

        print("  CapViz : set server's ip to : " + ip_textBox.text())

    ip_button.clicked.connect(connectToServer)

    def broadcast_border_ip():
        sendControlMessage('broadcast_border_ip')

    def get_ip_tables():
        sendControlMessage([], special_type='get_ip_table')

    ip_border_sync_nodes_button.clicked.connect(broadcast_border_ip)

    ip_border_get_ip_tables_button.clicked.connect(get_ip_tables)

    #  *******************************************************************  #
    #  ***************** SYSTEM CONTROL WIDGET ***************************  #
    #  *******************************************************************  #

    ## Add widgets into each dock

    ## first dock gets save/restore buttons
    w1 = pg.LayoutWidget()
    # label_0 = QtGui.QLabel(""" -- DockArea Example --
    # This window has 6 Dock widgets in it. Each dock can be dragged
    # by its title bar to occupy a different space within the window
    # but note that one dock has its title bar hidden). Additionally,
    # the borders between docks may be dragged to resize. Docks that are dragged on top
    # of one another are stacked in a tabbed layout. Double-click a dock title
    # bar to place it in its own window.
    # """)
    label_changing = QtGui.QLabel(""" 
        """)
    font = label_changing.font()
    font.setBold(True)
    label_changing.setFont(font)

    label_0 = QtGui.QLabel(""" -- Widget Buttons -- 
    """)
    saveBtn = QtGui.QPushButton('Save dock state')
    restoreBtn = QtGui.QPushButton('Restore dock state')

    label_1 = QtGui.QLabel(""" -- Sensing Control -- 
        """)
    startStream_Btn = QtGui.QPushButton('Start Streaming')
    stopStream_Btn = QtGui.QPushButton('Stop Streaming')

    label_2 = QtGui.QLabel(""" -- Data Collection -- 
            """)
    startLog_Btn = QtGui.QPushButton('Start Log')
    stopLog_Btn = QtGui.QPushButton('Stop Log')

    exitBtn = QtGui.QPushButton('EXIT')
    exitBtn.setStyleSheet("QPushButton { background-color: red }"
                      "QPushButton:pressed { background-color: blue }" )


    restoreBtn.setEnabled(False)
    w1.addWidget(label_0, row=0, col=0)
    w1.addWidget(saveBtn, row=1, col=0)
    w1.addWidget(restoreBtn, row=2, col=0)

    w1.addWidget(label_1, row=0, col=1)
    w1.addWidget(startStream_Btn, row=1, col=1)
    w1.addWidget(stopStream_Btn, row=2, col=1)

    w1.addWidget(label_2, row=0, col=2)
    w1.addWidget(startLog_Btn, row=1, col=2)
    w1.addWidget(stopLog_Btn, row=2, col=2)

    w1.addWidget(label_changing, row=3, col=0)

    # w1.addWidget(startEEG_Btn, row=3, col=1)
    # w1.addWidget(label_2, row=0, col=2)
    # w1.addWidget(stopFaceTrackingBtn, row=1, col=2)
    # w1.addWidget(stopEEG_Btn, row=3, col=2)

    w1.addWidget(exitBtn, row=3, col=2)
    d1.addWidget(w1)
    state = None


    EDA_state = 0
    EEG_state = 0
    OF_state = 0
    recording_state = 0
    collection_state = 0

    #  *******************************************************************  #
    #  ***************** LED CONTROL WIDGET ******************************  #
    #  *******************************************************************  #

    w_led_all = QtGui.QMainWindow()
    btn_led_all = pg.ColorButton()
    w_led_all.setCentralWidget(btn_led_all)
    w_led_all.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_all.addWidget(w_led_all)

    w_led_left_eye = QtGui.QMainWindow()
    btn_led_left_eye = pg.ColorButton()
    w_led_left_eye.setCentralWidget(btn_led_left_eye)
    w_led_left_eye.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_left_eye.addWidget(w_led_left_eye)

    w_led_right_eye = QtGui.QMainWindow()
    btn_led_right_eye = pg.ColorButton()
    w_led_right_eye.setCentralWidget(btn_led_right_eye)
    w_led_right_eye.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_right_eye.addWidget(w_led_right_eye)

    w_led_left_top = QtGui.QMainWindow()
    btn_led_left_top = pg.ColorButton()
    w_led_left_top.setCentralWidget(btn_led_left_top)
    w_led_left_top.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_left_top.addWidget(w_led_left_top)

    w_led_right_top = QtGui.QMainWindow()
    btn_led_right_top = pg.ColorButton()
    w_led_right_top.setCentralWidget(btn_led_right_top)
    w_led_right_top.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_right_top.addWidget(w_led_right_top)

    w_led_left_front = QtGui.QMainWindow()
    btn_led_left_front = pg.ColorButton()
    w_led_left_front.setCentralWidget(btn_led_left_front)
    w_led_left_front.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_left_front.addWidget(w_led_left_front)

    w_led_right_front = QtGui.QMainWindow()
    btn_led_right_front = pg.ColorButton()
    w_led_right_front.setCentralWidget(btn_led_right_front)
    w_led_right_front.show()
    # w_led.setWindowTitle('SYSTEM COLOR')
    d_led_right_front.addWidget(w_led_right_front)



    # def change(btn):
    #     print("change", btn.color(mode='byte'))

    def done(btn):
        print("done", btn.color(mode='byte')) # returns R, G, B, ALPHA

    def doneAll(btn):
        btn_led_left_eye.setColor(btn.color())
        btn_led_right_eye.setColor(btn.color())
        btn_led_left_top.setColor(btn.color())
        btn_led_right_top.setColor(btn.color())
        btn_led_left_front.setColor(btn.color())
        btn_led_right_front.setColor(btn.color())

        #print("done", btn.color(mode='byte')) # returns R, G, B, ALPHA

    LED_LEFT_FRONT_B = 1
    LED_LEFT_FRONT_G = 0
    LED_LEFT_TOP_B = 2
    LED_LEFT_TOP_G = 3
    LED_LEFT_SIDE_B = 4
    LED_LEFT_SIDE_G = 5
    LED_LEFT_FRONT_R = 6
    LED_LEFT_TOP_R = 7
    LED_LEFT_SIDE_R = 8

    LED_RIGHT_FRONT_B = 1
    LED_RIGHT_FRONT_G = 0
    LED_RIGHT_TOP_B = 2
    LED_RIGHT_TOP_G = 3
    LED_RIGHT_SIDE_B = 4
    LED_RIGHT_SIDE_G = 5
    LED_RIGHT_FRONT_R = 6
    LED_RIGHT_TOP_R = 7
    LED_RIGHT_SIDE_R = 8


    def setLED():
        # empty led color payloads
        payload_left = np.zeros(9)
        payload_right = np.zeros(9)

        # populate left payload
        payload_left[LED_LEFT_FRONT_R], payload_left[LED_LEFT_FRONT_G], payload_left[LED_LEFT_FRONT_B], _ = btn_led_left_front.color(mode='byte')
        payload_left[LED_LEFT_TOP_R], payload_left[LED_LEFT_TOP_G], payload_left[LED_LEFT_TOP_B], _ = btn_led_left_top.color(mode='byte')
        payload_left[LED_LEFT_SIDE_R], payload_left[LED_LEFT_SIDE_G], payload_left[LED_LEFT_SIDE_B], _ = btn_led_left_eye.color(mode='byte')

        # populate right payload
        payload_right[LED_RIGHT_FRONT_R], payload_right[LED_RIGHT_FRONT_G], payload_right[LED_RIGHT_FRONT_B], _ = btn_led_right_front.color(mode='byte')
        payload_right[LED_RIGHT_TOP_R], payload_right[LED_RIGHT_TOP_G], payload_right[LED_RIGHT_TOP_B], _ = btn_led_right_top.color(mode='byte')
        payload_right[LED_RIGHT_SIDE_R], payload_right[LED_RIGHT_SIDE_G], payload_right[LED_RIGHT_SIDE_B], _ = btn_led_right_eye.color(mode='byte')

        # combine payloads into a packet
        payload = np.concatenate((payload_left, payload_right), axis=None).astype(int)

        # pack-up payload into bytes
        payload_pack = pack('18B', *payload.tolist())

        # send payload to Coap server for messaging
        sendControlMessage(payload_pack, 'set_led')

    # button to push settings to captivates
    w_led_set = pg.LayoutWidget()
    setLED_btn = QtGui.QPushButton('SET LED')
    w_led_set.addWidget(setLED_btn, row=0, col=0)
    d_led_set.addWidget(w_led_set)
    state = None
    setLED_btn.clicked.connect(setLED)

    # # btn_led_right_front.sigColorChanging.connect(change)
    btn_led_left_eye.sigColorChanged.connect(done)
    btn_led_right_eye.sigColorChanged.connect(done)
    btn_led_left_top.sigColorChanged.connect(done)
    btn_led_right_top.sigColorChanged.connect(done)
    btn_led_left_front.sigColorChanged.connect(done)
    btn_led_right_front.sigColorChanged.connect(done)
    #
    btn_led_all.sigColorChanged.connect(doneAll)

    #  *******************************************************************  #
    #  ***************** CONTROL FUNCTIONS *******************************  #
    #  *******************************************************************  #


    def testNumber(value):
        global label_changing
        label_changing.setText(""" Test: %s""" % str(value))

    def save():
        global state
        state = area.saveState()
        restoreBtn.setEnabled(True)

    def load():
        global state
        area.restoreState(state)

    def startStream():
        global system_semaphore, blink_queue, temp_queue, pos_queue, inertial_queue, timer, data_collector_thread

        if data_collector_thread.is_alive():
            print(" CapViz : stream is already active")
        else:


            # tell Coap server where to send data to
            sendControlMessage(socket.gethostbyname(socket.gethostname()), 'set_data_ip')

            # tell Coap server to start streaming
            sendControlMessage('start_stream')

            # # start graph update time
            # timer.start(500)

            # grab semaphore and start running data collector
            # system_semaphore = threading.Semaphore()
            system_semaphore.acquire(blocking=False)
            time.sleep(.5) # give time for semaphore taken to be registered (sometimes its not immediate)
            #start_new_thread(runDataCollector, (system_semaphore, blink_queue, temp_queue, pos_queue, inertial_queue))
            data_collector_thread = threading.Thread(target=runDataCollector, args=(system_semaphore, blink_queue, temp_queue, pos_queue, inertial_queue,))
            data_collector_thread.start()

    # queues to update plots
    blink_queue = Queue()
    temp_queue = Queue()
    pos_queue = Queue()
    inertial_queue = Queue()
    def stopStream():
        global data_collector_thread, system_semaphore

        sendControlMessage('stop_stream')

        # # stop graph update time
        # timer.stop()

        if data_collector_thread.is_alive():
            # put semaphore back to tell data collector to stop
            system_semaphore.release()
            time.sleep(.2) # give time for the thread to finish
            print("joining")
            # data_collector_thread.raise_exception()
            data_collector_thread.join()
            print("joined thread")
        else:
            print("  CapViz : stream has already ended")

    def startLog():
        # tell Coap server where to send data to
        sendControlMessage(socket.gethostbyname(socket.gethostname()), 'set_data_ip')

        sendControlMessage('start_log')

    def stopLog():
        sendControlMessage('stop_log')


    def exitApplication():
        global collection_state

        print("exiting application")


        # app.exec_()
        QtGui.QApplication.instance().exec_()

        # QtGui.QApplication.exit()
        # QtGui.QApplication.processEvents()
        # pg.QtGui.QApplication.exec_()
        # app.quit()
        exit()


    def stopLog():
        sendControlMessage('stop_log')




    #  *******************************************************************  #
    #  ***************** BUTTON MAPPING **********************************  #
    #  *******************************************************************  #

    saveBtn.clicked.connect(save)
    restoreBtn.clicked.connect(load)

    startStream_Btn.clicked.connect(startStream)
    stopStream_Btn.clicked.connect(stopStream)

    startLog_Btn.clicked.connect(startLog)
    stopLog_Btn.clicked.connect(stopLog)

    exitBtn.clicked.connect(exitApplication)

    # saveBtn.clicked.connect(save)
    # restoreBtn.clicked.connect(load)
    # startFaceTrackingBtn.clicked.connect(startFaceTracking)
    # startEDA_Btn.clicked.connect(startEDA)
    # startEEG_Btn.clicked.connect(startEEG)
    # stopFaceTrackingBtn.clicked.connect(stopFaceTracking)
    # stopEDA_Btn.clicked.connect(stopEDA)
    # stopEEG_Btn.clicked.connect(stopEEG)
    # exitBtn.clicked.connect(exitApplication)
    # startCollectionBtn.clicked.connect(startCollection)
    # startCollectionVideoBtn.clicked.connect(startCollectionWithVid)
    # endCollectionBtn.clicked.connect(endCollection)
    #
    # w2 = pg.console.ConsoleWidget()
    #
    # ## Hide title bar on dock 3
    # d3.hideTitleBar()
    # w3 = pg.PlotWidget(title="Blink Activity")
    # #w3.plot(np.random.normal(size=100))
    # w3.setClipToView(True)
    # w3.setRange(xRange=[-1000, 0])
    # w3.setLimits(xMax=0)
    # eda_plot = w3.plot()
    #
    # blink_data = np.empty(1000)
    # blink_ptr = 0
    # d3.addWidget(w3)
    #
    # ## Hide title bar on dock 3
    # d2_2.hideTitleBar()
    # w2_2 = pg.PlotWidget(title="PPG Activity")
    # # w3.plot(np.random.normal(size=100))
    # w2_2.setClipToView(True)
    # w2_2.setRange(xRange=[-1000, 0])
    # w2_2.setLimits(xMax=0)
    # ppg_plot = w2_2.plot()
    #
    # ppg_plot_data = np.empty(1000)
    # ppg_ptr = 0
    # d3.addWidget(w2_2)


    #  *******************************************************************  #
    #  ***************** BLINK SPECIFIC **********************************  #
    #  *******************************************************************  #

    ## Hide title bar on dock 3
    d_blink.hideTitleBar()
    w_blink = pg.PlotWidget(title="Blink Activity")
    #w_blink.plot(np.random.normal(size=100))
    # w_blink.setClipToView(True)
    # w_blink.setRange(xRange=[-10000, 0])
    # w_blink.setLimits(xMax=0)
    # blink_plot = w_blink.plot()

    blink_data = np.empty(3000) #plotting 10,000 samples
    blink_time = np.empty(3000)

    blink_plot = w_blink.plot(blink_time, blink_data, pen='y', symbol='t', symbolPen=None, symbolSize=10, symbolBrush=(100, 100, 255, 50))

    w_blink.setLabel('left', "Blink Intensity")
    w_blink.setLabel('bottom', "Time", units='ms')

    blink_ptr = 0
    d_blink.addWidget(w_blink)

    #  *******************************************************************  #
    #  ***************** TEMP SPECIFIC ***********************************  #
    #  *******************************************************************  #

    ## Hide title bar on dock 3
    d_nose_temp.hideTitleBar()
    w_nose_temp = pg.PlotWidget(title="Nose Temp")
    # w_nose_temp.plot(np.random.normal(size=100))
    # w_nose_temp.setClipToView(True)
    # # w_nose_temp.setRange(xRange=[-3000, 0])
    # w_nose_temp.setLimits(xMax=0)

    d_temple_temp.hideTitleBar()
    w_temple_temp = pg.PlotWidget(title="Temple Temp")
    # w_temple_temp.plot(np.random.normal(size=100))
    w_temple_temp.setClipToView(True)
    # # w_temple_temp.setRange(xRange=[-3000, 0])
    # w_temple_temp.setLimits(xMax=0)

    d_diff_temp.hideTitleBar()
    w_diff_temp = pg.PlotWidget(title="Delta Temp")
    # w_diff_temp.plot(np.random.normal(size=100))
    w_diff_temp.setClipToView(True)
    # # w_diff_temp.setRange(xRange=[-3000, 0])
    # w_diff_temp.setLimits(xMax=0)


    nose_temp_data = np.empty(200)
    temple_temp_data = np.empty(200)
    diff_temp_data = np.empty(200)

    temp_ptr = 0

    nose_temp_time = np.empty(200)
    temple_temp_time = np.empty(200)
    diff_temp_time = np.empty(200)

    nose_temp_plot = w_nose_temp.plot(nose_temp_time, nose_temp_data, pen=(255,0,0), name="Red curve")
    temple_temp_plot = w_temple_temp.plot(temple_temp_time, temple_temp_data, pen=(0, 255, 0), name="Green curve")
    diff_temp_plot = w_diff_temp.plot(diff_temp_time, diff_temp_data, pen=(0, 0, 255), name="Blue curve")

    d_nose_temp.addWidget(w_nose_temp)
    d_temple_temp.addWidget(w_temple_temp)
    d_diff_temp.addWidget(w_diff_temp)


    #  *******************************************************************  #
    #  ***************** INERTIAL SPECIFIC ******************************  #
    #  *******************************************************************  #



    quat_real = 0.0
    quat_i = 0.0
    quat_j = 0.0
    quat_k = 0.0
    activity_class = "Unknown"

    label_quaternion = QtGui.QLabel("\t**Quaternion**")
    label_inertial_real = QtGui.QLabel("\tReal:")
    label_inertial_i = QtGui.QLabel("\ti")
    label_inertial_j = QtGui.QLabel("\tj")
    label_inertial_k = QtGui.QLabel("\tk")
    label_inertial_activity = QtGui.QLabel("   **Most Probable Activity**")
    label_activity_confidences = QtGui.QLabel("\t**Activity Confidences**")

    label_3d_location = QtGui.QLabel("\t**3D Location**")
    x_loc = 0
    y_loc = 0
    z_loc = 0
    line_x_loc = QtGui.QLabel()
    line_y_loc = QtGui.QLabel()
    line_z_loc = QtGui.QLabel()
    line_x_loc.setText("\tx: " + str(x_loc))
    line_y_loc.setText("\ty: " + str(y_loc))
    line_z_loc.setText("\tz: " + str(z_loc))

    label_inertial_activity_0 = QtGui.QLabel("\t" + activityClasses[0])
    label_inertial_activity_1 = QtGui.QLabel("\t" + activityClasses[1])
    label_inertial_activity_2 = QtGui.QLabel("\t" + activityClasses[2])
    label_inertial_activity_3 = QtGui.QLabel("\t" + activityClasses[3])
    label_inertial_activity_4 = QtGui.QLabel("\t" + activityClasses[4])
    label_inertial_activity_5 = QtGui.QLabel("\t" + activityClasses[5])
    label_inertial_activity_6 = QtGui.QLabel("\t" + activityClasses[6])
    label_inertial_activity_7 = QtGui.QLabel("\t" + activityClasses[7])
    label_inertial_activity_8 = QtGui.QLabel("\t" + activityClasses[8])


    # line_quat_real = QLineEdit(server_IP)
    # line_quat_i = QLineEdit(server_IP)
    # line_quat_j = QLineEdit(server_IP)
    # line_quat_k = QLineEdit(server_IP)
    # line_activity = QLineEdit(activity_class)

    # line_quat_real = pg.ValueLabel()
    # line_quat_i = pg.ValueLabel(siPrefix=True, suffix='i')
    # line_quat_j = pg.ValueLabel(siPrefix=True, suffix='j')
    # line_quat_k = pg.ValueLabel(siPrefix=True, suffix='k')
    # line_activity = pg.ValueLabel()

    line_quat_real = QtGui.QLabel()
    line_quat_i = QtGui.QLabel()
    line_quat_j = QtGui.QLabel()
    line_quat_k = QtGui.QLabel()
    line_activity = QtGui.QLabel()

    line_quat_real.setText(str(quat_real))
    line_quat_i.setText(str(quat_i) + "\ti")
    line_quat_j.setText(str(quat_j) + "\tj")
    line_quat_k.setText(str(quat_k) + "\tk")
    line_activity.setText("\t" + str(activity_class))

    activityVector = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    line_activity_0 = QtGui.QLabel()
    line_activity_1 = QtGui.QLabel()
    line_activity_2 = QtGui.QLabel()
    line_activity_3 = QtGui.QLabel()
    line_activity_4 = QtGui.QLabel()
    line_activity_5 = QtGui.QLabel()
    line_activity_6 = QtGui.QLabel()
    line_activity_7 = QtGui.QLabel()
    line_activity_8 = QtGui.QLabel()

    line_activity_0.setText(str(activityVector[0]))
    line_activity_1.setText(str(activityVector[1]))
    line_activity_2.setText(str(activityVector[2]))
    line_activity_3.setText(str(activityVector[3]))
    line_activity_4.setText(str(activityVector[4]))
    line_activity_5.setText(str(activityVector[5]))
    line_activity_6.setText(str(activityVector[6]))
    line_activity_7.setText(str(activityVector[7]))
    line_activity_8.setText(str(activityVector[8]))

    # d_inertial.addWidget(label_inertial_real, 1, 0)
    # d_inertial.addWidget(label_inertial_i, 2, 0)
    # d_inertial.addWidget(label_inertial_j, 3, 0)
    # d_inertial.addWidget(label_inertial_k, 4, 0)
    # d_inertial.addWidget(label_inertial_activity, 5, 0)
    #
    # d_inertial.addWidget(line_quat_real, 1, 2)
    # d_inertial.addWidget(line_quat_i, 2, 2)
    # d_inertial.addWidget(line_quat_j, 3, 2)
    # d_inertial.addWidget(line_quat_k, 4, 2)
    # d_inertial.addWidget(line_activity, 5, 2)

    d_inertial.addWidget(label_quaternion, 0, 0)
    d_inertial.addWidget(line_quat_real, 1, 0)
    d_inertial.addWidget(line_quat_i, 2, 0)
    d_inertial.addWidget(line_quat_j, 3, 0)
    d_inertial.addWidget(line_quat_k, 4, 0)
    d_inertial.addWidget(label_inertial_activity, 7, 0)
    d_inertial.addWidget(line_activity, 8, 0)

    d_inertial.addWidget(label_activity_confidences, 0, 2)
    d_inertial.addWidget(label_inertial_activity_0, 1, 2)
    d_inertial.addWidget(label_inertial_activity_1, 2, 2)
    d_inertial.addWidget(label_inertial_activity_2, 3, 2)
    d_inertial.addWidget(label_inertial_activity_3, 4, 2)
    d_inertial.addWidget(label_inertial_activity_4, 5, 2)
    d_inertial.addWidget(label_inertial_activity_5, 6, 2)
    d_inertial.addWidget(label_inertial_activity_6, 7, 2)
    d_inertial.addWidget(label_inertial_activity_7, 8, 2)
    d_inertial.addWidget(label_inertial_activity_8, 9, 2)

    d_inertial.addWidget(line_activity_0, 1, 3)
    d_inertial.addWidget(line_activity_1, 2, 3)
    d_inertial.addWidget(line_activity_2, 3, 3)
    d_inertial.addWidget(line_activity_3, 4, 3)
    d_inertial.addWidget(line_activity_4, 5, 3)
    d_inertial.addWidget(line_activity_5, 6, 3)
    d_inertial.addWidget(line_activity_6, 7, 3)
    d_inertial.addWidget(line_activity_7, 8, 3)
    d_inertial.addWidget(line_activity_8, 9, 3)

    d_inertial.addWidget(label_3d_location,0,4)
    d_inertial.addWidget(line_x_loc, 1, 4)
    d_inertial.addWidget(line_y_loc, 2, 4)
    d_inertial.addWidget(line_z_loc, 3, 4)


    # w4 = pg.PlotWidget(title="Dock 4 plot")
    # w4.plot(np.random.normal(size=100))
    # d4.addWidget(w4)

    # w5 = pg.ImageView()
    # w5.setImage(np.random.normal(size=(100, 100)))
    # d5.addWidget(w5)

    # w6 = pg.PlotWidget(title="Dock 6 plot")
    # w6.plot(np.random.normal(size=100))
    # d6.addWidget(w6)

    ## Hide title bar on dock 3
    # d7.hideTitleBar()
    # w7 = pg.PlotWidget(title="Blink")
    # # w3.plot(np.random.normal(size=100))
    # w7.setClipToView(True)
    # w7.setRange(xRange=[-200, 0])
    # w7.setLimits(xMax=0)
    #
    # d8.hideTitleBar()
    # w8 = pg.PlotWidget(title="Blink Intensity")
    # # w3.plot(np.random.normal(size=100))
    # w8.setClipToView(True)
    # w8.setRange(xRange=[-200, 0])
    # w8.setLimits(xMax=0)
    #
    # blink_plot = w7.plot(pen=(255, 0, 255), name="Red curve")
    # blink_intensity_plot = w8.plot(pen=(255, 255, 0), name="Green curve")
    #
    # blink_plot_data = np.empty(300)
    # blink_intensity_plot_data = np.empty(300)
    # blink_ptr = 0
    #
    # d7.addWidget(w7)
    # d8.addWidget(w8)

    ## Hide title bar on dock 3
    # d9.hideTitleBar()
    # w9 = pg.PlotWidget(title="Gaze Angle X")
    # # w3.plot(np.random.normal(size=100))
    # w9.setClipToView(True)
    # w9.setRange(xRange=[-200, 0])
    # w9.setLimits(xMax=0)
    #
    # d10.hideTitleBar()
    # w10 = pg.PlotWidget(title="Gaze Angle Y")
    # # w3.plot(np.random.normal(size=100))
    # w10.setClipToView(True)
    # w10.setRange(xRange=[-200, 0])
    # w10.setLimits(xMax=0)
    #
    # eye_angle_x_plot = w9.plot(pen=(255, 0, 0), name="Red curve")
    # eye_angle_y_plot = w10.plot(pen=(0, 255, 0), name="Green curve")
    #
    # eye_angle_x_plot_data = np.empty(300)
    # eye_angle_y_plot_data = np.empty(300)
    # eye_ptr = 0

    # d9.addWidget(w9)
    # d10.addWidget(w10)



    # app = QtGui.QApplication([])
    # win = pg.GraphicsWindow()
    # win.setWindowTitle('Learner\'s Measurements')
    # p1 = win.addPlot()
    # p1.setClipToView(True)
    # p1.setRange(xRange=[-100, 0])
    # p1.setLimits(xMax=0)
    # eda_plot = p1.plot()
    #
    # eda_plot_data = np.empty(300)
    # eda_ptr = 0

    #
    # def update_EDA_plot(new_val):
    #     global eda_plot_data, eda_ptr, eda_plot
    #
    #     eda_plot_data[eda_ptr] = new_val
    #     eda_ptr += 1
    #     if eda_ptr >= eda_plot_data.shape[0]:
    #         tmp = eda_plot_data
    #         eda_plot_data = np.empty(eda_plot_data.shape[0] * 2)
    #         eda_plot_data[:tmp.shape[0]] = tmp
    #     eda_plot.setData(eda_plot_data[:eda_ptr])
    #     eda_plot.setPos(-eda_ptr, 0)
    #     QtGui.QApplication.processEvents()
    #
    # def update_PPG_plot(new_val):
    #     global ppg_plot_data, ppg_ptr, ppg_plot
    #
    #     ppg_plot_data[ppg_ptr] = new_val
    #     ppg_ptr += 1
    #     if ppg_ptr >= ppg_plot_data.shape[0]:
    #         tmp = ppg_plot_data
    #         ppg_plot_data = np.empty(ppg_plot_data.shape[0] * 2)
    #         ppg_plot_data[:tmp.shape[0]] = tmp
    #     ppg_plot.setData(ppg_plot_data[:ppg_ptr])
    #     ppg_plot.setPos(-ppg_ptr, 0)
    #     QtGui.QApplication.processEvents()
    #
    #
    # def update_EEG_plot(new_val_1, new_val_2):
    #     global eeg_plot_data_1, eeg_plot_data_2, eeg_ptr, eeg_plot_1, eeg_plot_2
    #
    #     eeg_plot_data_1[eeg_ptr] = new_val_1
    #     eeg_plot_data_2[eeg_ptr] = new_val_2
    #     eeg_ptr += 1
    #
    #     if eeg_ptr >= eeg_plot_data_1.shape[0]:
    #         tmp = eeg_plot_data_1
    #         eeg_plot_data_1 = np.empty(eeg_plot_data_1.shape[0] * 2)
    #         eeg_plot_data_1[:tmp.shape[0]] = tmp
    #
    #         tmp = eeg_plot_data_2
    #         eeg_plot_data_2 = np.empty(eeg_plot_data_2.shape[0] * 2)
    #         eeg_plot_data_2[:tmp.shape[0]] = tmp
    #
    #     eeg_plot_1.setData(eeg_plot_data_1[:eeg_ptr]) #, fftMode=True
    #     eeg_plot_1.setPos(-eeg_ptr, 0)
    #
    #     eeg_plot_2.setData(eeg_plot_data_2[:eeg_ptr]) #, fftMode=True
    #     eeg_plot_2.setPos(-eeg_ptr, 0)
    #
    #     QtGui.QApplication.processEvents()
    #
    # def update_OF_movement_plot(new_val):
    #     global of_plot_movement_data, of_movement_ptr, of_movement_plot
    #
    #     of_plot_movement_data[of_movement_ptr] = new_val
    #     of_movement_ptr += 1
    #
    #     if of_movement_ptr >= of_plot_movement_data.shape[0]:
    #         tmp = of_plot_movement_data
    #         of_plot_movement_data = np.empty(of_plot_movement_data.shape[0] * 2)
    #         of_plot_movement_data[:tmp.shape[0]] = tmp
    #
    #     of_movement_plot.setData(of_plot_movement_data[:of_movement_ptr])
    #     of_movement_plot.setPos(-of_movement_ptr, 0)
    #
    #     QtGui.QApplication.processEvents()


    def update_OF_blink_plot(blink_queue):
        global blink_data, blink_time, blink_ptr, blink_plot



        blink_ptr = 0

        while True:
            [new_blink_data, new_blink_time] = blink_queue.get()

            # if data is empty, continue
            if (new_blink_data[0] == 0):
                continue

            # make room for new data in buffer
            blink_data = np.roll(blink_data, -1 * len(new_blink_data))


            blink_time_array = np.arange(blink_ptr, blink_ptr+len(new_blink_data))
            blink_ptr += len(new_blink_data)

            blink_time = np.roll(blink_time, -1 * len(blink_time_array))

            # add new data by replacing the last n'th samples in buffer
            blink_data[(len(blink_data)-len(new_blink_data)):] = new_blink_data
            # print(blink_time_array)
            # print(blink_ptr)
            # print(len(new_blink_data))
            # if(len(blink_time_array) > 1):
            blink_time[(len(blink_data)-len(blink_time_array)):] = blink_time_array

            # blink_time[(len(blink_data)-len(new_blink_data)):] = new_blink_time

            # blink_data.append(blink_sample)
            #
            # blink_data[blink_ptr] = eye_blink
            # blink_ptr += 1

            # # if pointer exceeds data buffer size
            # if blink_ptr >= blink_data.shape[0]:
            #     # store current buffer somewhere temporary
            #     tmp = blink_data
            #     # while we create new buffer that is twice the size
            #     blink_data = np.empty(blink_data.shape[0] * 2)
            #     # and then put the old data back in
            #     blink_data[:tmp.shape[0]] = tmp

            # # we are now going to put part of the data into the plot
            # blink_plot.setData(blink_data[:blink_ptr]) # , fftMode=True
            # # and set the position of the plot
            # blink_plot.setPos(-blink_ptr, 0)


            blink_plot.setData(blink_time, blink_data)

            # if blink_ptr == autoscale_stop_sample:
            #     blink_plot.enableAutoRange('xy', False)  ## stop auto-scaling after the "autoscale_stop_sample"

            # update the plots
            QtGui.QApplication.processEvents()

    def update_OF_temp_plot(temp_queue):
        global nose_temp_data, temple_temp_data, diff_temp_data
        global nose_temp_time, temple_temp_time, diff_temp_time
        global temp_ptr
        global nose_temp_plot, temple_temp_plot, diff_temp_plot



        while True:
            # print("TEMP: WAITING")
            [new_nose_temp_data, new_temple_temp_data, new_temp_time] = temp_queue.get()

            # if data is empty, break
            if (new_nose_temp_data == 0 and new_temple_temp_data == 0):
                continue

            # print("TEMP PACKET RECEIVED")
            # print(new_nose_temp_data)
            # print(new_temp_time)

            # make room for new data in buffer
            nose_temp_data = np.roll(nose_temp_data, -1)
            nose_temp_time = np.roll(nose_temp_time, -1)

            temple_temp_data = np.roll(temple_temp_data, -1)

            diff_temp_data = np.roll(diff_temp_data, -1)

            # add new data by replacing the last n'th samples in buffer
            nose_temp_data[-1] = new_nose_temp_data
            nose_temp_time[-1] = new_temp_time

            temple_temp_data[-1] = new_temple_temp_data
            temple_temp_time[-1] = new_temp_time

            diff_temp_data[-1] = new_nose_temp_data - new_temple_temp_data
            diff_temp_time[-1] = new_temp_time

            # blink_data.append(blink_sample)
            #
            # blink_data[blink_ptr] = eye_blink
            # blink_ptr += 1

            # # if pointer exceeds data buffer size
            # if blink_ptr >= blink_data.shape[0]:
            #     # store current buffer somewhere temporary
            #     tmp = blink_data
            #     # while we create new buffer that is twice the size
            #     blink_data = np.empty(blink_data.shape[0] * 2)
            #     # and then put the old data back in
            #     blink_data[:tmp.shape[0]] = tmp

            # # we are now going to put part of the data into the plot
            # blink_plot.setData(blink_data[:blink_ptr]) # , fftMode=True
            # # and set the position of the plot
            # blink_plot.setPos(-blink_ptr, 0)

            nose_temp_plot.setData(nose_temp_time, nose_temp_data)
            temple_temp_plot.setData(nose_temp_time, temple_temp_data)
            diff_temp_plot.setData(nose_temp_time, diff_temp_data)

            # if blink_ptr == autoscale_stop_sample:
            #     blink_plot.enableAutoRange('xy', False)  ## stop auto-scaling after the "autoscale_stop_sample"

            # update the plots
            QtGui.QApplication.processEvents()

    def update_OF_inertial_plot(inertial_queue):
        global quat_real, quat_i, quat_j, quat_k, activity_class
        # global nose_temp_time, temple_temp_time, diff_temp_time
        # global temp_ptr
        # global nose_temp_plot, temple_temp_plot, diff_temp_plot

        while True:
            # print("TEMP: WAITING")
            [quat_real, quat_i, quat_j, quat_k, activity_class] = inertial_queue.get()

            # if data is empty, break
            if (quat_i == 0 and quat_j == 0 and quat_k == 0 ):
                continue

            # print(activity_class)

            line_quat_real.setText(' ' + str(quat_real))
            line_quat_i.setText(' ' + str(quat_i) + '\ti')
            line_quat_j.setText(' ' + str(quat_j) + '\tj')
            line_quat_k.setText(' ' + str(quat_k) + '\tk')

            # # Separate out the confidence vector
            try:
                activityVector = np.array(activity_class)
            except:
                print(" CapViz : ACTIVITY VECTOR EMPTY or NOT 9 BYTES")

            if(len(activityVector) == 9):
                line_activity_0.setText(str(activityVector[0]))
                line_activity_1.setText(str(activityVector[1]))
                line_activity_2.setText(str(activityVector[2]))
                line_activity_3.setText(str(activityVector[3]))
                line_activity_4.setText(str(activityVector[4]))
                line_activity_5.setText(str(activityVector[5]))
                line_activity_6.setText(str(activityVector[6]))
                line_activity_7.setText(str(activityVector[7]))
                line_activity_8.setText(str(activityVector[8]))
                #
                # # Find what the greatest confidence activity is
                activity_class = activityClasses[np.where(activityVector == np.amax(activityVector))[0][0]]
                line_activity.setText('\t' + str(activity_class))

            QtGui.QApplication.processEvents()

    def send_loc_to_vis(x, y, z, accuracy, time):
        # as a client, tell COAP server to tell glasses to start streaming
        # host = socket.gethostname()
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #
        # # connect to COAP server on local computer
        # s.connect(('', port_loc_vis))
        #
        # s.send([x, y, z])
        #
        # s.close()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', port_loc_vis))
            packet = pack("fff", x, y, z)
            s.sendall(packet)
            # data = s.recv(1024)

        # x = 2

    def update_OF_pos_plot(pos_queue):
        # global quat_real, quat_i, quat_j, quat_k, activity_class
        # global nose_temp_time, temple_temp_time, diff_temp_time
        # global temp_ptr
        # global nose_temp_plot, temple_temp_plot, diff_temp_plot

        while True:
            # print("TEMP: WAITING")
            [pos_x, pos_y, pos_z, pos_accuracy, time_ms_pos] = pos_queue.get()

            # print(str(pos_x) + "\t" + str(pos_y) + "\t" + str(pos_z))
            if (pos_x == 0 and pos_y == 0 and pos_z == 0):
                continue
            print(str(pos_x) + "\t" + str(pos_y) + "\t" + str(pos_z))

            # loc_visualizer_queue.put
            send_loc_to_vis(pos_x, pos_y, pos_z, pos_accuracy, time_ms_pos)

            # line_quat_real.setText(' ' + str(quat_real))
            # line_quat_i.setText(' ' + str(quat_i) + '\ti')
            # line_quat_j.setText(' ' + str(quat_j) + '\tj')
            # line_quat_k.setText(' ' + str(quat_k) + '\tk')

            if(len(activityVector) == 9):
                line_x_loc.setText("\tx: " + str(pos_x))
                line_y_loc.setText("\ty: " + str(pos_y))
                line_z_loc.setText("\tz: " + str(pos_z))

            QtGui.QApplication.processEvents()

    # def update_OF_eye_angle_plot(eye_angle_x, eye_angle_y):
    #     global eye_angle_x_plot_data, eye_angle_y_plot_data, eye_ptr, eye_angle_x_plot, eye_angle_y_plot
    #
    #     eye_angle_x_plot_data[eye_ptr] = eye_angle_x
    #     eye_angle_y_plot_data[eye_ptr] = eye_angle_y
    #     eye_ptr += 1
    #
    #     if eye_ptr >= eye_angle_x_plot_data.shape[0]:
    #         tmp = eye_angle_x_plot_data
    #         eye_angle_x_plot_data = np.empty(eye_angle_x_plot_data.shape[0] * 2)
    #         eye_angle_x_plot_data[:tmp.shape[0]] = tmp
    #
    #         tmp = eye_angle_y_plot_data
    #         eye_angle_y_plot_data = np.empty(eye_angle_y_plot_data.shape[0] * 2)
    #         eye_angle_y_plot_data[:tmp.shape[0]] = tmp
    #
    #     eye_angle_x_plot.setData(eye_angle_x_plot_data[:eye_ptr]) # , fftMode=True
    #     eye_angle_x_plot.setPos(-eye_ptr, 0)
    #
    #     eye_angle_y_plot.setData(eye_angle_y_plot_data[:eye_ptr]) #, fftMode=True
    #     eye_angle_y_plot.setPos(-eye_ptr, 0)
    #
    #     QtGui.QApplication.processEvents()

    win.show()
    QtGui.QApplication.processEvents()

    # timer.start(100)

    # function to update plots
    # def update_plots():
    #     print('update')
    #     global QtGui
    #     QtGui.QApplication.processEvents()
    #
    # # timer to update plots
    # # timer = QtCore.QTimer()
    # # timer.timeout.connect(update)
    #
    # timer_plot_update = threading.Timer(0.2, update_plots)

    # timer_plot_update.start()

    # start sensor updater threads updater

    start_new_thread(update_OF_blink_plot, (blink_queue, ))

    start_new_thread(update_OF_temp_plot, (temp_queue,))

    start_new_thread(update_OF_inertial_plot, (inertial_queue,))

    start_new_thread(update_OF_pos_plot, (pos_queue,))

    # def viz_check():
    #     x = 0
    #     y = 0
    #     z = 0
    #     while True:
    #         x += 1
    #         y += 1
    #         z += 1
    #         time.sleep(1)
    #         send_loc_to_vis(x, y, z, 0, 0)
    #
    # start_new_thread(viz_check, ())

    index = 0

    get_ip_timer = threading.Timer(30.0, get_ip_tables)
    get_ip_timer.start()

    while True:
        try:
            # try:
            #     openFace_data = openface_queue.get(block=False)
            # except queue.Empty:
            #     # Handle empty queue here
            #     pass
            # else:
            #     update_OF_movement_plot(openFace_data['face_movement'])
            #     update_OF_blink_plot(openFace_data['AU45_c'], openFace_data['AU45_r'])
            #     update_OF_eye_angle_plot(openFace_data['gaze_angle_x'], openFace_data['gaze_angle_y'])
            #     #y_vec_2[-1] = openFace_data['AU45_c']
            #     #line2 = live_plotter(x_vec_2, y_vec_2, line2)
            #     #y_vec_2 = np.append(y_vec_2[1:], 0.0)
            #     pass
            #
            #
            # try:
            #     eeg_data = EEG_queue.get(block=False)
            # except queue.Empty:
            #     # Handle empty queue here
            #     pass
            # else:
            #     update_EEG_plot(eeg_data[1][0], eeg_data[1][1])
            #     #y_vec_2[-1] = openFace_data['AU45_c']
            #     #line2 = live_plotter(x_vec_2, y_vec_2, line2)
            #     #y_vec_2 = np.append(y_vec_2[1:], 0.0)
            #     pass
            #
            #
            # try:
            #     EDA_data = EDA_queue.get(block=False)
            # except queue.Empty:
            #     # Handle empty queue here
            #     pass
            # else:
            #     update_EDA_plot(EDA_data['GSR'])
            #     update_PPG_plot(EDA_data['PPG'])
            #     #y_vec[-1] = EDA_data['GSR']
            #     #line1 = live_plotter(x_vec, y_vec, line1)
            #     #y_vec = np.append(y_vec[1:], 0.0)
            #     pass
            #print("put")
            time.sleep(.1)
            # update_OF_blink_plot(np.random.rand(100), np.arange(index,index+100))
            # blink_queue.put([np.random.rand(100),  np.arange(index,index+100)])
            # index += 100
            QtGui.QApplication.processEvents()

        except KeyboardInterrupt:
            print('interrupt received')
            # openface_queue_alert.put('q')
            print('joining processes')
            print('done')
            QtGui.QApplication.instance().exec_()

    #pg.QtGui.QApplication.exec_()  # you MUST put this at the end
   # app.quit()
   #  QtGui.QApplication.exit()
   #  app.exec_()
    QtGui.QApplication.instance().exec_()


