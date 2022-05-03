from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logic
import dialog
import Util


#
#   Input configuration dialog
#   Starts with given initial configuration and calls on "ok" the given
#   callback function to notify / update the main ui

class InputConfig:
    # button minimum height
    buttonHeight = 50

    # input config
    config = None

    # return callback
    callback = None

    # frequency label
    frequencyNumber = None

    # ui elements
    dialog = None
    frequencyPick = None

    #
    #   set all ui elements to the current
    #   setting in self.input
    def updateView(self):
        pretty = Util.printFreq(self.config.frequency)
        self.frequencyNumber.setText(pretty[0] + " " + pretty[1])

        # set checked
        self.enabled.setChecked(self.config.enabled)


    #
    #   frequency change button clicked
    #   launch frequency picker dialog
    def frequencyClicked(self, num):
        print("set frequency")
        min = logic.Constants.INPUT_F_MIN
        max = 0
        if (self.config.format == logic.InputFormat.STANDARD):
            max = logic.Constants.INPUT_F_MAX_DIFF
        else:
            max = logic.Constants.INPUT_F_MAX_CMOS

        dialog.FreqPicker(lambda f: self.frequencyChanged(f), self.config.frequency, (min, max))

    #
    #   callback from frequency dialog
    #   write new frequency in config variable
    def frequencyChanged(self, f):
        print("set frequency " + str(f))
        self.config.frequency = f
        self.updateView()

    #
    #   input channel seletion changed
    #
    def enabledChange(self, checked):
        print("enable checked: " + str(checked))
        self.config.enabled = checked
        # TODO HIDE
        self.updateView()

    #
    #   exit button used
    #   reject settings and close dialog
    def exitDialog(self):
        self.callback(self.config)
        self.dialog.accept()

    #
    # create ui
    #
    def createConfig(self):
        self.dialog = QDialog()
        layout = QGridLayout()

        # title
        label = QLabel(Util.styleText("Input configuration", 25, bold=True))
        layout.addWidget(label, 0, 0, 1, 3)

        # exit
        exit = QPushButton("")
        exit.clicked.connect(lambda: self.dialog.reject())
        exit.setMinimumHeight(self.buttonHeight)
        pixmapi = QStyle.SP_BrowserStop
        exit.setIcon(exit.style().standardIcon(pixmapi))
        layout.addWidget(exit, 0, 3)

        # channel
        inputLabel = QLabel("Enabled")
        layout.addWidget(inputLabel, 1, 0, 1, 2)
        self.enabled = QCheckBox("")
        self.enabled.setStyleSheet("QCheckBox::indicator{width: 35px;height: 35px;}")
        self.enabled.setChecked(self.config.enabled)
        self.enabled.stateChanged.connect(self.enabledChange)
        self.enabled.setMinimumHeight(self.buttonHeight)
        layout.addWidget(self.enabled, 1, 3, 1, 1)

        # frequency
        frequencyLabel = QLabel("Input frequency")
        layout.addWidget(frequencyLabel, 2, 0, 1, 2)

        pretty = Util.printFreq(self.config.frequency)
        self.frequencyNumber = QLabel(pretty[0] + " " + pretty[1])
        self.frequencyNumber.setMinimumHeight(self.buttonHeight)
        layout.addWidget(self.frequencyNumber, 2, 2, 1, 1)

        self.frequencyPick = QPushButton("Set")
        self.frequencyPick.setMinimumHeight(self.buttonHeight)
        self.frequencyPick.clicked.connect(lambda: self.frequencyClicked(0))
        layout.addWidget(self.frequencyPick, 2, 3, 1, 1)

        # ok
        ok = QPushButton("Ok")
        ok.clicked.connect(self.exitDialog)
        ok.setMinimumHeight(self.buttonHeight)
        layout.addWidget(ok, 5, 3, 1, 1)

        # prepare window
        for i in range(layout.rowCount()):
            layout.setRowStretch(i,1)

        for i in range(layout.columnCount()):
            layout.setColumnStretch(i,1)

        frame = QFrame()
        frame.setLayout(layout)
        frameLayout = QVBoxLayout()
        frameLayout.addWidget(frame)
        frame.setFrameShape(QFrame.Box)
        frame.setLineWidth(2)
        self.dialog.setLayout(frameLayout)
        self.dialog.setStyleSheet("font-size: 25px;")
        self.dialog.setWindowTitle("InputDialog")
        self.dialog.setObjectName("InputDialog");
        self.dialog.setMinimumSize(600,300)
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup);
        print("created frequency picker")
        self.updateView()
        self.dialog.exec_()

    def __init__(self, callback, input):
        self.callback = callback
        self.config = input
        self.createConfig()
