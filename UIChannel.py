#!/bin/python3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import dialog
import Util
import logic


#
#   This class represents one user interface output channel
#   All channel related functionality is handled in this class
#   Init: Configuration.OutputChannel + Channel name
#
class UIChannel():

    #
    #   set on off button image + text
    #
    def setButtonUI(self):
        if(self.channel.enabled):
            pixmapi = QStyle.SP_MediaPlay
            self.onOff.setChecked(True)
            self.onOff.setIcon(self.onOff.style().standardIcon(pixmapi))
            self.onOff.setText("On")
        else:
            pixmapi = QStyle.SP_MediaStop
            self.onOff.setChecked(False)
            self.onOff.setIcon(self.onOff.style().standardIcon(pixmapi))
            self.onOff.setText("Off")

    #
    #   User toggled the on off button
    def onOffClicked(self):
        self.channel.enabled = self.onOff.isChecked()
        print("channel " + str(self.channel.index) + " enabled now " + str(self.onOff.isChecked()))
        self.configUpdate()

    #
    #   Update the clock generator chip
    #   configuration
    #   call callback to the taktUi class
    def configUpdate(self, callback=True):
        self.setButtonUI()
        self.formatLabel.setText(Util.printFormat(self.config, self.channel.index))
        self.freqLabel.setText(
            "Target:\n{}\nReal:\n{}".format(
                "".join(Util.printFreq(self.channel.frequency)),
                "".join(Util.printFreq(self.channel.realFrequency))
            ))
        self.setButtonUI()
        if callback==True:
            self.callback(self.channel.index)

    #
    #   The set frequency button is clicked
    #   starts the "FreqPicker" dialog and set callback handler
    def frequencyClicked(self):
        print("launch frequency picker for channel " + str(self.channel.index))

        min = logic.Constants.OUTPUT_F_MIN
        max = 0
        if (self.channel.signal.type == logic.SignalType.LVCMOS_INPHASE or
            self.channel.signal.type == logic.SignalType.LVCMOS_COMPL):
            max = logic.Constants.OUTPUT_F_MAX_CMOS
        else:
            max = logic.Constants.OUTPUT_F_MAX_DIFF

        dialog.FreqPicker(lambda f: self.frequencyChangedCallback(f), self.channel.frequency, (min, max))

    #
    #   set frequency dialog callback
    #   only called when result confirmed with ok
    def frequencyChangedCallback(self, f):
        print("set frequency " + str(f) + " for channel " + str(self.channel.index))
        self.channel.frequency = f
        self.configUpdate()

    #
    #   The format selection button is clicked
    #   starts the "FormatConfig" dialog and sets callback handler
    def formatClicked(self):
        print("launch format picker for channel " + str(self.channel.index))
        dialog.FormatConfig(lambda ch: self.formatChangedCallback(ch), self.config, self.channel.index)

    #
    #   set format dialog callback
    #   only called when result confirmed with ok
    def formatChangedCallback(self, format):
        print("formatChangedCallback " + str(format))
        self.channel.signal = format
        self.configUpdate()

    #
    #   UIChannel init function
    #   creates all UI elements and sets values from given channel config
    def __init__(self, channel, config, callback, info):
        self.callback = callback
        self.config = config
        self.frame = QFrame()
        self.layout = QVBoxLayout()
        self.channel = channel

        name = "{}".format(info)
        self.title = QLabel(Util.styleText(name, 25, bold=True))
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)

        # on off
        self.onOff = QPushButton()
        self.onOff.setCheckable(True)
        self.onOff.setChecked(channel.enabled)
        self.onOff.clicked.connect(lambda: self.onOffClicked())
        self.onOff.setMinimumHeight(50)
        self.setButtonUI()
        self.layout.addWidget(self.onOff)

        # frequency
        freqWidget = QGroupBox("Frequency")
        freqLayout = QVBoxLayout()

        self.freqLabel = QLabel(
            "Target:\n{}\nReal:\n{}".format(
                "".join(Util.printFreq(self.channel.frequency)),
                "".join(Util.printFreq(self.channel.realFrequency))
            ))
        freqLayout.addWidget(self.freqLabel)
        self.frequency = QPushButton("set")
        self.frequency.clicked.connect(lambda: self.frequencyClicked())
        freqLayout.addWidget(self.frequency)
        freqWidget.setLayout(freqLayout)
        self.layout.addWidget(freqWidget)

        # signal format
        formatWidget = QGroupBox("Signal Format")
        formatWidget.setMinimumHeight(210)
        formatLayout = QVBoxLayout()
        self.formatLabel = QLabel(Util.printFormat(self.config, self.channel.index))
        self.formatLabel.setWordWrap(True)
        formatLayout.addWidget(self.formatLabel)
        self.format = QPushButton("set")
        self.format.clicked.connect(lambda: self.formatClicked())
        formatLayout.addWidget(self.format)
        formatWidget.setLayout(formatLayout)
        self.layout.addWidget(formatWidget)

        self.frame.setLayout(self.layout)
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setLineWidth(2)
