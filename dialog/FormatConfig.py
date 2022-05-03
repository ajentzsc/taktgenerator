from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import dialog
import Util
import logic.Config as Config
import logic


#
#   Format configuration dialog
#   Starts with given initial configuration and calls on "ok" the given
#   callback function to notify / update the main ui

class FormatConfig:
    minHeight = 50

    # return callback
    callback = None

    # selection options
    formatOptions = [val.value for val in Config.SignalType]

    # voltage options
    voltageOptions = logic.Constants.VOLT_OPTIONS

    # termination options
    terminationOptions = logic.Constants.TERM_OPTIONS

    # ui elements
    formatSelect = None
    voltageLabel = None
    voltageSelect = None
    terminationLabel = None
    terminationSelect = None

    # current configuration
    format = None

    # dialog
    dialog = None

    # lock all value change listener to prevent trigger loop
    # is True during updateUI(). When lock is asserted updateUI()
    # should not be called
    # do not modify
    lock = False

    # find index of current voltage value in available values
    def voltageIndex(self):
        return self.voltageOptions.index(self.config.vddo.value)

    # find index of current format value in available values
    def formatIndex(self):
        return self.formatOptions.index(self.format.type.value)

    #
    #   update ui to match the current configuration
    #
    def updateUI(self):
        self.lock = True
        # set voltage selection
        self.voltageSelect.clear()
        for option in self.voltageOptions:
            self.voltageSelect.addItem(option)
        self.voltageSelect.setCurrentIndex(self.voltageIndex())

        # show termination selection only for LVCMOS_INPHASE / LVCMOS_COMPL
        if (self.format.type == Config.SignalType.LVCMOS_INPHASE or
            self.format.type == Config.SignalType.LVCMOS_COMPL):
            self.terminationLabel.setVisible(True)
            self.terminationSelect.setVisible(True)
            self.voltageSelect.setVisible(True)
            self.voltageLabel.setVisible(True)
        else:
            self.terminationLabel.setVisible(False)
            self.terminationSelect.setVisible(False)
            self.voltageSelect.setVisible(False)
            self.voltageLabel.setVisible(False)

        # set format selection
        self.formatSelect.setCurrentIndex(self.formatIndex())

        # set termination selection
        self.terminationSelect.clear()
        for option in self.terminationOptions[self.voltageIndex()]:
            self.terminationSelect.addItem(option)
        self.terminationSelect.setCurrentIndex(self.format.impedance)

        # reset termination to lowest index in case the old index
        # doesnt fit in the new selection list
        if (self.format.impedance >= len(self.terminationOptions[self.voltageIndex()])):
            self.format.impedance = 0
            self.terminationSelect.setCurrentIndex(0)
        self.lock = False

    #
    #   the signal format selection changed
    #   only change format selection when valid format & frequency combination
    def formatSelectionChange(self, i):
        if not self.lock:
            print("format seleted: " + self.formatOptions[i])
            newFormat = Config.SignalType(self.formatOptions[i])

            if (newFormat == Config.SignalType.LVCMOS_INPHASE or
                newFormat == Config.SignalType.LVCMOS_COMPL):
                # check for violation of maximum frequency
                if (self.config.channels[self.index].frequency > logic.Constants.OUTPUT_F_MAX_CMOS):
                    freqText = Util.printFreq(logic.Constants.OUTPUT_F_MAX_CMOS)
                    dialog.GenericDialog(
                        "Maximum frequency violated",
                        "Please choose for CMOS output frequency less or equal " + freqText[0] + " " + freqText[1] + ".",
                        dialog.GenericDialogType.OK
                    )
                    self.updateUI() # reject changes
                    return

            self.format.type = Config.SignalType(self.formatOptions[i])
            self.updateUI()

    #
    #   lists all voltage collisions
    #   collisions can occur when another CMOS output is configured
    #   or an HCSL output is configured and the user wants to add a CMOS
    #   output with VDDO = 1.8V
    def listVoltageCollisions(self, newVoltage):
        collisions = []
        for channel in self.config.channels:
            if self.index == channel.index:
                # currently configured channel
                continue

            if (channel.signal.type == logic.SignalType.LVDS
                or channel.signal.type == logic.SignalType.LVPECL):
                # independent from voltage
                continue

            if (channel.signal.type == logic.SignalType.HCSL):
                # HCSL not at 1.8V
                if newVoltage != logic.SignalVoltage.V1P8:
                    continue

            collisions.append(channel)

        return collisions

    #
    # callback from the voltage collision warning
    # change other channel CMOS outputs when the user want the new VDDO
    # TODO change HCSL output to ?
    def voltageCollisionCallback(self, agreed):
        print("voltageCollisionCallback " + str(agreed))
        if agreed:
            # list collisions
            collisions = self.listVoltageCollisions(self.vTmp)

            # look for channel with HCSL that is incompatible
            # with 1.8V vddo
            if self.vTmp == logic.SignalVoltage.V1P8:
                for coll in collisions:
                    if coll.signal.type == logic.SignalType.HCSL:
                        # HCSL has no 1.8V option --> change to LVDS
                        self.config.channels[coll.index].signal.type = logic.SignalType.LVDS

            # change vddo
            self.config.vddo = self.vTmp

        self.updateUI()

    #
    # different voltage selected
    # this device has only one vddo, so there are no different CMOS outputs
    # possible. This function checks whether the new selected voltage collides
    # with another configured CMOS output.
    def voltageSelectionChange(self, i):
        if not self.lock:
            collisions = self.listVoltageCollisions(self.voltageOptions[i])
            self.vTmp = Config.SignalVoltage(self.voltageOptions[i])

            if (len(collisions) == 0):
                print("voltage seleted: " + self.voltageOptions[i])
                self.config.vddo = Config.SignalVoltage(self.voltageOptions[i])
                self.updateUI()
            else:
                # build message
                dialogTitle = "Voltage collision detected"
                dialogMessage = ""
                outputList = "{}".format(collisions[0].index)
                for i in range(1, len(collisions)-1):
                    outputList = outputList + ", {}".format(collisions[i].index)

                if (len(collisions)>1):
                    dialogMessage = "The channels {} currently use a different VDDO ({}).\n" \
                        "All outputs must have the same VDDO.\n" \
                        "Do you want to change the voltage of channels {}\n" \
                        "to keep your selection?"
                else:
                    dialogMessage = "The channel {} currently uses a different VDDO ({}).\n" \
                        "All outputs must have the same VDDO.\n" \
                        "Do you want to change the voltage of channel {}\n" \
                        "to keep your selection?"

                dialogMessage = dialogMessage.format(
                    outputList,
                    self.config.vddo,
                    outputList
                )

                dialog.GenericDialog(dialogTitle, dialogMessage, dialog.GenericDialogType.YES_NO, self.voltageCollisionCallback)

    # new termination selected
    def terminationSelectionChange(self, i):
        if not self.lock:
            print("termination seleted: " + self.terminationOptions[self.voltageIndex()][i])
            self.format.impedance = i
            self.updateUI()

    # exit button clicked
    def exitDialog(self):
        self.callback(self.format)
        self.dialog.accept()

    # create ui
    def createConfig(self):
        self.dialog = QDialog()
        layout = QGridLayout()

        # title
        label = QLabel(Util.styleText("Format configuration", 25, bold=True))
        layout.addWidget(label, 0, 0, 1, 3)
        print(self.format)

        # exit
        exit = QPushButton("")
        exit.clicked.connect(lambda: self.dialog.reject())
        exit.setMinimumHeight(50)
        pixmapi = QStyle.SP_BrowserStop
        exit.setIcon(exit.style().standardIcon(pixmapi))
        layout.addWidget(exit, 0, 3, 1, 1)

        # format
        formatLabel = QLabel("Format selection")
        layout.addWidget(formatLabel, 1, 0, 1, 2)
        self.formatSelect = QComboBox()
        for option in self.formatOptions:
            self.formatSelect.addItem(option)
        self.formatSelect.setCurrentIndex(self.formatIndex())
        self.formatSelect.currentIndexChanged.connect(self.formatSelectionChange)
        self.formatSelect.setMinimumHeight(self.minHeight)
        layout.addWidget(self.formatSelect, 1, 2, 1, 2)

        # voltage
        self.voltageLabel = QLabel("Voltage")
        layout.addWidget(self.voltageLabel, 2, 0, 1, 2)
        self.voltageSelect = QComboBox()
        self.voltageSelect.setMinimumHeight(self.minHeight)
        self.voltageSelect.currentIndexChanged.connect(self.voltageSelectionChange)
        layout.addWidget(self.voltageSelect, 2, 2, 1, 2)

        # termination
        self.terminationLabel = QLabel("Termination")
        layout.addWidget(self.terminationLabel, 3, 0, 1, 2)
        self.terminationSelect = QComboBox()
        self.terminationSelect.currentIndexChanged.connect(self.terminationSelectionChange)
        self.terminationSelect.setMinimumHeight(self.minHeight)
        self.terminationLabel.setVisible(False)
        self.terminationSelect.setVisible(False)
        layout.addWidget(self.terminationSelect, 3, 2, 1, 2)

        # ok
        ok = QPushButton("Ok")
        ok.setMinimumHeight(self.minHeight)
        ok.clicked.connect(self.exitDialog)
        layout.addWidget(ok, 4, 3)

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
        self.dialog.setWindowTitle("FormatDialog")
        self.dialog.setObjectName("FormatDialog");
        self.dialog.setMinimumSize(500,400)
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup);
        print("created format picker")
        self.updateUI()
        self.dialog.exec_()


    # the active FormatConfiguration
    def __init__(self, callback, config, index):
        self.callback = callback
        self.index = index
        self.config = config
        self.vTmp = None
        if self.config.channels[index].signal == None:
            self.config.channels[index].signal = Config.SignalFormat(Config.SignalType.LVDS, config.DisabledState.STOP_LOW, Config.SignalVoltage.V1P8, 0)
        self.format = self.config.channels[index].signal
        self.createConfig()
