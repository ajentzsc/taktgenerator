from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import Util
from enum import Enum


#
#   Dialog type
#
class GenericDialogType(Enum):
    YES_NO = 1  # user choice
    OK  = 2     # user ack
    YES_NO_ABORT = 3 # user choice + break


#
#   Generic dialog with multiple answer patterns
#   possible answer patterns declared in enum GenericDialogType
#   Dialog is not dismissable, on user selection the callback is called with
#   True / False
class GenericDialog:

    # current dialog type
    dialogType = GenericDialogType.OK

    # callback when finished
    callback = None

    # this qt dialog
    dialog = None

    # answer ok / yes
    def answerYes(self):
        if self.callback != None:
            self.callback(True)
        self.dialog.reject()

    # answer no
    def answerNo(self):
        if self.callback != None:
            self.callback(False)
        self.dialog.reject()

    # answer exit
    def answerAbort(self):
        if self.callback != None:
            self.callback(None)
        self.dialog.reject()

    # create ui
    def createDialog(self, title, message):
        self.dialog = QDialog()
        layout = QVBoxLayout()

        # title
        label = QLabel(Util.styleText(title, 25, bold=True))
        layout.addWidget(label)

        # message
        content = QLabel(message)
        layout.addWidget(content)

        # options
        options = QWidget()
        optionLayout = QHBoxLayout()

        if self.dialogType == GenericDialogType.YES_NO or self.dialogType == GenericDialogType.YES_NO_ABORT:
            yes = QPushButton("Yes")
            yes.clicked.connect(self.answerYes)
            yes.setMinimumHeight(50)
            optionLayout.addWidget(yes)

            no = QPushButton("No")
            no.clicked.connect(self.answerNo)
            no.setMinimumHeight(50)
            optionLayout.addWidget(no)

            if self.dialogType == GenericDialogType.YES_NO_ABORT:
                abort = QPushButton("Abort")
                abort.clicked.connect(self.answerAbort)
                abort.setMinimumHeight(50)
                optionLayout.addWidget(no)

        elif self.dialogType == GenericDialogType.OK:
            ok = QPushButton("Ok")
            ok.clicked.connect(self.answerYes)
            ok.setMinimumHeight(50)
            optionLayout.addWidget(ok)


        options.setLayout(optionLayout)
        layout.addWidget(options)

        frame = QFrame()
        frame.setLayout(layout)
        frameLayout = QVBoxLayout()
        frameLayout.addWidget(frame)
        frame.setFrameShape(QFrame.Box)
        frame.setLineWidth(2)
        self.dialog.setLayout(frameLayout)
        self.dialog.setStyleSheet("font-size: 25px;")
        self.dialog.setWindowTitle("GenericDialog")
        self.dialog.setObjectName("GenericDialog")
        self.dialog.setProperty("class", "GenericDialog");
        self.dialog.setMinimumSize(400,300)
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup);
        print("created GenericDialog")
        self.dialog.exec_()

    def __init__(self, title, message, type=GenericDialogType.OK, callback=None):
        self.callback = callback
        self.dialogType = type
        self.createDialog(title, message)
