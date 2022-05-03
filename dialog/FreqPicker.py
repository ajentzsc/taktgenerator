from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logic.Constants as Constants
import Util
import dialog

#
#   Frequency configuration dialog
#   Starts with given initial configuration and calls on "ok" the given
#   callback function to notify / update the main ui

class FreqPicker:
    # numpad button height
    buttonHeight = 55

    # frequency float
    frequency = 0

    # callback when finished
    callback = None

    # frequency qlabel
    freq = None

    # unit qlabel
    unit = None

    # this qt dialog
    dialog = None

    # update internal float frequency
    def updateFreq(self):
        if len(str(self.freq.text()).strip()) > 0:
            self.frequency = float(str(self.freq.text()))
        else:
            self.frequency = 0.0

    # single digit
    def numberClicked(self, num):
        text = self.freq.text()
        if (text == "0"):
            text = str(num)
        else:
            text += str(num)
        self.freq.setText(text)
        self.updateFreq()

    # decimal point
    def pointClicked(self):
        text = self.freq.text()
        if "." not in text:
            if len(str(text).strip()) == 0:
                text += "0."
            else:
                text += "."
        self.freq.setText(text)
        self.updateFreq()

    # delete last digit
    def deleteClicked(self):
        if len(str(self.freq.text())) > 0:
            text = str(self.freq.text())[0:-1]
            self.freq.setText(text)
            self.updateFreq()

    # set unit
    def hertzClicked(self, hz):
        print("hertz: " + str(hz))
        self.unit.setText(hz)
        self.updateFreq()

    #
    #   check frequency bounds
    #
    def checkBounds(self, floatFreq):
        print(str(floatFreq))
        if floatFreq < float(self.minMax[0]):
            # lower bound
            freqText = Util.printFreq(self.minMax[0])
            dialog.GenericDialog(
                "Minimum frequency violated",
                "Please choose at least" + freqText[0] + " " + freqText[1] + ".",
                dialog.GenericDialogType.OK
            )
            return False

        if floatFreq > float(self.minMax[1]):
            # higher bound
            freqText = Util.printFreq(self.minMax[1])
            dialog.GenericDialog(
                "Maximium frequency violated",
                "Please choose frequency below" + freqText[0] + " " + freqText[1] + ".",
                dialog.GenericDialogType.OK
            )
            return False
        return True

    # result callback
    def okClicked(self):
        # add unit
        self.updateFreq()
        floatFreq = 0
        if str(self.unit.text()) == Constants.KHZ:
            floatFreq = self.frequency * 1000
        elif str(self.unit.text()) == Constants.MHZ:
            floatFreq = self.frequency * 1000_000
        else:
            floatFreq = self.frequency

        # check bounds, only return when ok
        if self.checkBounds(floatFreq):
            self.callback(floatFreq)
            self.dialog.accept()

    # create ui
    def createPicker(self):
        self.dialog = QDialog()
        layout = QGridLayout()

        # title
        label = QLabel(Util.styleText("Choose frequency", 25, bold=True))
        layout.addWidget(label, 0, 0, 1, 3)

        # exit
        exit = QPushButton("")
        exit.clicked.connect(lambda: self.dialog.reject())
        exit.setMinimumHeight(50)
        pixmapi = QStyle.SP_BrowserStop
        exit.setIcon(exit.style().standardIcon(pixmapi))
        layout.addWidget(exit, 0, 3)

        # frequency
        if (self.frequency == 0.0):
            self.freq = QLabel("0")
            self.unit = QLabel(Constants.HZ)
        else:
            pretty = Util.printFreq(self.frequency)
            self.freq = QLabel(str(pretty[0]))
            self.unit = QLabel(pretty[1])
        layout.addWidget(self.freq, 1, 0, 1, 3)
        layout.addWidget(self.unit, 1, 3)

        # min max
        if (self.minMax[0] != 0):
            min = Util.printFreq(self.minMax[0])
            max = Util.printFreq(self.minMax[1])
            self.bounds = QLabel("({}{}  - {}{} )".format(min[0],min[1],max[0],max[1]))
            self.bounds.setStyleSheet("font-size: 15px;")
            layout.addWidget(self.bounds, 2, 0, 1, 3)

        # number
        for i in range(1,10):
            button = QPushButton(str(i))
            button.clicked.connect(lambda state, i=i: self.numberClicked(i))
            button.setAutoRepeat(True)
            button.setAutoRepeatDelay(750)
            button.setAutoRepeatInterval(100)
            button.setMinimumHeight(self.buttonHeight)
            layout.addWidget(button, 3+((i-1)//3), (i-1)%3)

        # point
        point = QPushButton(".")
        point.clicked.connect(lambda: self.pointClicked())
        point.setMinimumHeight(self.buttonHeight)
        layout.addWidget(point, 6, 0)

        # zero
        zero = QPushButton("0")
        zero.clicked.connect(lambda: self.numberClicked(0))
        zero.setMinimumHeight(self.buttonHeight)
        layout.addWidget(zero, 6, 1)

        # delete
        delete = QPushButton("\u2190") # left arrow mark symbol
        delete.setAutoRepeat(True)
        delete.setAutoRepeatDelay(400)
        delete.setAutoRepeatInterval(100)
        delete.clicked.connect(lambda: self.deleteClicked())
        delete.setMinimumHeight(self.buttonHeight)
        layout.addWidget(delete, 6, 2)

        # hz
        hz = QPushButton(Constants.HZ)
        hz.clicked.connect(lambda: self.hertzClicked(Constants.HZ))
        hz.setMinimumHeight(self.buttonHeight)
        layout.addWidget(hz, 3, 3)

        khz = QPushButton(Constants.KHZ)
        khz.clicked.connect(lambda: self.hertzClicked(Constants.KHZ))
        khz.setMinimumHeight(self.buttonHeight)
        layout.addWidget(khz, 4, 3)

        mhz = QPushButton(Constants.MHZ)
        mhz.clicked.connect(lambda: self.hertzClicked(Constants.MHZ))
        mhz.setMinimumHeight(self.buttonHeight)
        layout.addWidget(mhz, 5, 3)

        # ok
        ok = QPushButton("Ok")
        ok.clicked.connect(lambda: self.okClicked())
        ok.setMinimumHeight(self.buttonHeight)
        layout.addWidget(ok, 6, 3)

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
        self.dialog.setWindowTitle("FrequencyDialog")
        self.dialog.setObjectName("FrequencyDialog")
        self.dialog.setProperty("class", "FrequencyDialog");
        self.dialog.setMinimumSize(500,400)
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup);
        print("created frequency picker")
        self.dialog.exec_()

    def __init__(self, callback, frequency=0, minMax=(0.0, float("inf"))):
        self.callback = callback
        self.frequency = frequency
        self.minMax = minMax
        self.createPicker()
