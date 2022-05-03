#!/bin/python3
import pickle
import os.path as path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import platform

import Util
import UIChannel
import logic
import dialog
import Worker

#
#   Start class
#   This class manages the UI, adds the per channel UI and handles the menu
#   All configuration changes trigger the "configChangedCallback" function
#   This class starts on other systems thaan the raspi as windowed gui
class TaktUI():

    #
    #   exit button OnClick Listener
    #
    def exitClicked(self):
        print("exit")
        self.worker.exit(self.app)
        os.system("sudo shutdown now")

    #
    #   lockUpdate
    #   This is called from the Worker
    def lockUpdate(self, text):
        self.stateLabel.setText(text)

    #
    #   progressUpdate
    #   This is called from the Worker
    def progressUpdate(self, text):
        self.infoLabel.setText("Progress:\n" + text)

    #
    #   callback for set input dialog
    #   when: new input configuration
    def inputChangedCallback(self, input):
        self.conf.inputs[input.index] = input
        print("set input " + str(self.conf.inputs) + " callback return")
        self.configChangedCallback(-1)

    #
    #   updates the input button text
    #
    def setInputText(self):
        for i in range(len(self.inputButtons)):
            name = logic.Constants.IN_NAMES[i] + "\n"
            if (self.conf.inputs[i].enabled):
                self.inputButtons[i].setText(name + "".join(Util.printFreq(self.conf.inputs[i].frequency)).strip())
            else:
                self.inputButtons[i].setText(name + "OFF")

    #
    #   start input configuration dialog
    #
    def inputClicked(self, index):
        dialog.InputConfig(self.inputChangedCallback, self.conf.inputs[index])

    #
    #   Callback from one of the channel classes
    #   signaling that the configuration has changed
    #   call with index = -1 when loading configuration
    def configChangedCallback(self, index):
        print("Channel " + str(index) + " config has changed ")

        # update configuration in worker
        self.worker.config = self.conf

        # only when output channel active
        if self.conf.hasActiveChannel() or (index == -1):
            # recalculate divider
            self.conf = logic.calcDivider(self.conf)
            for uiChannel in self.channels:
                # update channel dataset from global dataset
                uiChannel.channel = self.conf.channels[uiChannel.channel.index]
                # refresh ui values
                uiChannel.configUpdate(False)
            print("new divider ")

            # set register to match configuration
            self.conf = logic.setRegister(self.conf)

            # transmit settings
            self.worker.writeConfig(self.conf)
        else:
            # no active channel
            self.worker.powerDown()

        self.setInputText()

        return


    #
    #   Save current configuration to file
    #   to binary config file
    def saveClicked(self):
        print("save config to file" + logic.Constants.CONFIG_FILE)
        with open(logic.Constants.CONFIG_FILE, 'wb') as f:
            pickle.dump(self.conf, f)
        self.progressUpdate("saved config")

    #
    #   Open previously saved configuration
    #   and update user interface
    def openClicked(self):
        print("load config from file" + logic.Constants.CONFIG_FILE)
        if not path.exists(logic.Constants.CONFIG_FILE):
            dialog.GenericDialog("Info", "No configuration file.")
            return

        # read file
        with open(logic.Constants.CONFIG_FILE, 'rb') as f:
            self.conf = pickle.load(f)
            print(self.conf)

        # disable all outputs
        for chan in self.conf.channels:
            chan.enabled = False

        # update ui + register
        self.configChangedCallback(-1)

        self.progressUpdate("loaded config")

    #
    #   creates button with given name,
    #   symbol and callback function
    #   the callback argument is optional
    def createButton(self, name, symbol, function, arg=None, height=50):
        button = QPushButton(name)
        button.setMinimumHeight(height)
        pixmapi = symbol
        button.setIcon(self.window.style().standardIcon(pixmapi))
        if arg != None:
            button.clicked.connect(lambda: function(arg))
        else:
            button.clicked.connect(function)
        return button


    #
    #   Generates the side menu
    #   Called at startup
    def __createMenu(self):
        self.menu = QFrame()
        layout = QVBoxLayout()

        # Save button
        layout.addWidget(self.createButton("Save", QStyle.SP_DialogSaveButton, self.saveClicked, height=60))

        # open button
        layout.addWidget(self.createButton("Load", QStyle.SP_DirIcon, self.openClicked, height=60))

        # input buttons
        self.inputButtons = []
        for i in range(len(logic.Constants.IN_NAMES)):
            inButton = self.createButton(logic.Constants.IN_NAMES[i], QStyle.SP_CommandLink, self.inputClicked, i, height=80)
            inButton.setStyleSheet("text-align:left;")
            layout.addWidget(inButton)
            self.inputButtons.append(inButton)
        self.setInputText()

        # info label
        self.infoLabel = QLabel("startup")
        self.infoLabel.setWordWrap(True)
        layout.addWidget(self.infoLabel)

        # lol / los state label
        self.stateLabel = QLabel("startup")
        self.stateLabel.setWordWrap(True)
        layout.addWidget(self.stateLabel)

        # power off
        layout.addWidget(self.createButton("OFF", QStyle.SP_BrowserStop, self.exitClicked))

        self.menu.setLayout(layout)
        return self.menu


    #
    #   init ui
    #
    def __init__(self):
        self.app = QApplication([])
        self.window = QWidget()
        # default values
        self.conf = logic.Configuration([
            logic.OutChannel(0, 20000000, False, logic.SignalFormat(logic.SignalType.LVDS, logic.DisabledState.STOP_LOW, 0)),
            logic.OutChannel(1, 20000000, False, logic.SignalFormat(logic.SignalType.LVDS, logic.DisabledState.STOP_LOW, 0)),
            logic.OutChannel(2, 20000000, False, logic.SignalFormat(logic.SignalType.LVDS, logic.DisabledState.STOP_LOW, 0)),
            logic.OutChannel(3, 20000000, False, logic.SignalFormat(logic.SignalType.LVDS, logic.DisabledState.STOP_LOW, 0)),
            ],[
            logic.Input(0),
            logic.Input(1)
            ])

        # generate layout
        self.layout = QHBoxLayout()
        self.channels = [
            UIChannel.UIChannel(self.conf.channels[0], self.conf, self.configChangedCallback, "CLK 0\nSide J2/3"),   # fmc board CLKO_0
            UIChannel.UIChannel(self.conf.channels[1], self.conf, self.configChangedCallback, "CLK 1\nSide J4/5"),   # fmc board CLKO_1
            UIChannel.UIChannel(self.conf.channels[3], self.conf, self.configChangedCallback, "CLK 2\nBottom J1/2"), # mother board GBTCLK0 SWITCHED
            UIChannel.UIChannel(self.conf.channels[2], self.conf, self.configChangedCallback, "CLK 3\nBottom J3/4")  # mother board CLK_M2C
        ]

        # size layout
        for channel in self.channels:
            self.layout.addWidget(channel.frame,0)
            channel.frame.setMaximumWidth(190)
        menue = self.__createMenu()
        menue.setMinimumWidth(200)
        self.layout.addWidget(menue,100)
        self.window.setLayout(self.layout)
        self.window.setStyleSheet("font-size: 22px;")
        self.window.show()

        if ("arm" in platform.machine()):
            # Raspberry
            print("running on raspberry")
            print("using touch configuration")
            self.window.setWindowState(Qt.WindowFullScreen)
            # hide cursor
            cursor = QCursor(Qt.BlankCursor)
            self.app.setOverrideCursor(cursor)
            self.app.changeOverrideCursor(cursor)
        else:
            # Desktop fallback
            print("running on desktop")
            print("using mouse configuration")
            self.window.setFixedSize(1024, 600)

        #
        #   initiate worker
        #   this worker handles the timeconsuming tasks
        self.worker = Worker.Worker(self.conf)
        self.worker.lockUpdate.connect(self.lockUpdate)
        self.worker.progressUpdate.connect(self.progressUpdate)

        self.app.exec()


#
#   main code
#
taktUI = TaktUI()
