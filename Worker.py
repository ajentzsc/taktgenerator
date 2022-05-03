#!/bin/python3
import logic
import platform
import time
import Util
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject
from threading import Thread
from threading import Timer

#
#   This worker class runs all time consuming tasks on another thread
#   there is only 1 thread to prevent multiple thread writing / reading
#   the SPI / GPIO interface
#   There is also a "queue" with one place to hold the next command.
#   This item is with every next call overwritten and deleted when
#   the worker thread finished processing it
class Worker(QObject):

    # Signals
    lockUpdate = pyqtSignal(str)
    progressUpdate = pyqtSignal(str)

    #
    #   read status and clear register
    #   RUNS ON WORKER
    def __updateStatus(self):
        if not "arm" in platform.machine(): return
        status = self.spi.readStatus()
        text = Util.printLocked(self.config, status)
        self.lockUpdate.emit(text)
        self.__clearFlags()

    #
    #   read Si5394 status from spi connection
    #
    def updateStatus(self):
        self.__threadingWrapper(self.__updateStatus, [])

    #
    #   Callback from GPIO module
    #   when: INTR --> LOL or LOS or ...
    def gpioChanged(self, lol, los):
        #print("gpioChanged: " + text)
        self.__threadingWrapper(self.__clearFlags, [])


    #
    #   Callback from spi module
    #   when transmission finished
    def spiCallback(self, info):
        pass

    #
    #   starts the given function on new thread
    #   when worker still working   --> return False
    #   when worker started         --> return True
    def __threadingWrapper(self, function, args=None):
        if self.worker == None or not self.worker.is_alive():
            # print("starting new thread for running " + str(function))
            if args == None:
                self.worker = Thread(target=function)
            else:
                self.worker = Thread(target=function, args=args)
            self.worker.start()
            return True
        else:
            # add next command to queue
            if len(self.queue) < 10:
                print("worker thread already running, adding to queue {}".format(len(self.queue)))
                self.queue.append((function, args))
            else:
                print("worker thread already running, queue to long, aborting.")
            return False

    #
    #   starting point for write config
    #   returns false when worker already running
    def writeConfig(self, conf):
        return self.__threadingWrapper(self.__writeConfig, [conf])

    #
    #   reset LOS / LOL from the UI thread
    #
    def clearFlags(self):
        self.__threadingWrapper(self.__clearFlags, [])

    #
    #   clear interrupt flags
    #   to remove interrupt and react to new changes
    def __clearFlags(self):
        map = logic.RegisterMap()
        message = [
            map.SYSINCAL_FLG,
            map.LOSXAXB_FLG,
            map.XAXB_ERR_FLG,
            map.SMBUS_TIMEOUT_FLG,
            map.LOS_FLG,
            map.OOF_FLG,
            map.LOL_FLG,
            map.HOLD_FLG,
            map.CAL_FLG_PLL
        ]   # leave initial value 0, just clearing
        self.spi.writeRegister(map.buildTransferList(message))
        self.__checkQueue()

    #
    #   transmit configuration
    #   RUNS ON WORKER
    def __writeConfig(self, conf):
        print("started writeConfig")
        #print(conf)

        # prepare configuration transmission list
        register = conf.regMap.buildTransferList()

        # disable outputs
        self.progressUpdate.emit("disable output")
        self.gpio.setOutput(False)

        # set GPIO output voltage
        # set voltage
        self.progressUpdate.emit("set voltage")
        self.gpio.setVoltage(conf.vddo)

        # write spi config
        self.progressUpdate.emit("write register")
        self.spi.writeRegister(register)

        # enable outputs
        self.progressUpdate.emit("enable output")
        self.gpio.setOutput(True)

        # enable LEDS on active channels
        self.gpio.illumChannel(conf)
        self.progressUpdate.emit("finished")

        self.__checkQueue()

    #
    #   powerdown device, for exit or when no output in use
    #   RUNS ON WORKER
    def __powerDown(self):
        # powerdown device
        self.progressUpdate.emit("power down")
        message = logic.RegisterMap().PDN
        message.val = 0x1 # powerdown
        self.spi.writeRegister(message.bytes()) # write config
        for led in range(6):
            self.gpio.setLed(led, False) # LEDS off
        self.__checkQueue()

    #
    #   powerdown device, for exit or when no output in use
    #
    def powerDown(self):
        return self.__threadingWrapper(self.__powerDown, [])

    #
    #   perform shutdown tasks
    #   gets reference to the current window to close it
    def exit(self, app):
        return self.__threadingWrapper(self.__exit, [app])

    #
    #   power down clock generator
    #   and close / reset all connections
    #   RUNS ON WORKER
    def __exit(self, app):

        # stop update timer
        self.timer.cancel()

        if ("arm" in platform.machine()):
            self.__powerDown()

            self.progressUpdate.emit("close gpio")
            self.gpio.close()

            self.progressUpdate.emit("close spi")
            self.spi.close()
        else:
            self.progressUpdate.emit("shutdown")

        # close window
        app.quit()

    #
    #   Do startup asynchronous
    #   RUNS ON WORKER
    def __start(self):
        if ("arm" in platform.machine()):
            # Raspberry
            self.gpio = logic.GPIOControl(self.gpioChanged)
            self.spi = logic.Connection(self.spiCallback)

            self.progressUpdate.emit("reset device")
            self.gpio.resetDevice()     # initiate reset

            self.progressUpdate.emit("enable led")
            self.gpio.setLed(6,True)    # signal ready
            self.progressUpdate.emit("ready")

        else:
            # Desktop
            self.progressUpdate.emit("reset gpio")
            self.gpio = None
            time.sleep(2)

            self.progressUpdate.emit("enable led")
            time.sleep(2)
            self.spi  = None
            self.progressUpdate.emit("ready")

        self.__checkQueue()

    #
    #   Check for queued configuration and transmit
    #   RUNS ON WORKER THREAD
    def __checkQueue(self):
        # user changed configuration --> transmit
        while self.queue != []:
            print("found item in queue --> transmit")

            # copy next item and
            # delete queue element
            nextCommand = self.queue[0]
            self.queue.pop(0)

            # call queued function with arguments
            # (function, args)
            nextCommand[0](*nextCommand[1])

    #
    #   init worker
    #
    def __init__(self, config):
        super().__init__()
        self.config = config            # configuration
        self.worker = Thread(target=self.__start)
        self.worker.start()

        # timer to update the los / lol info
        # repeats every 2 seconds + uses worker thread
        self.timer = Util.RepeatTimer(2, self.updateStatus)
        self.timer.start()

        self.queue = []   # list of next commands: [(function, [arg0, arg1 ...])]
