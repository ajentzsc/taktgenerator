#!/bin/python3
import logic
import time

#
#
#   This script writes the CBpro export csv files
#   to the Clockbuilder. It uses the Taktgenerator
#   codebase without GUI
#   The path of the file is set in the variable "file"
#
#

class WriteRegisterFile():

    #
    #   Callback from GPIO module
    #   when: INTR --> LOL or LOS or ...
    def gpioChanged(self, lol, los):
        text ="LOL: {} LOS: {}".format(lol,los)
        print("gpioChanged: " + text)

    #
    #   Callback from SPI module
    #   when: Transmission information
    def spiCallback(self, message):
        print("spi callback " + str(message))

        # enable outputs
        self.gpio.setOutput(True)

        # enable LEDS on active channels
        # self.gpio.illumChannel(self.conf)

    #
    # read register file
    #
    def readRegister(self, file):
        f = open(file, "r")
        lines = f.readlines()
        toggleRead = False
        register = []
        for line in lines:
            if line.__contains__("configuration registers"):
                toggleRead = not toggleRead
                continue

            if toggleRead:
                segments = line.split(",")
                register.append((int(segments[0], 16), int(segments[1], 16)))
        return register



    #
    #   init test
    #
    def __init__(self):

        #
        # init
        #
        self.gpio = logic.GPIOControl(self.gpioChanged)
        self.spi = logic.Connection(self.spiCallback)

        self.gpio.resetDevice()     # initiate reset
        time.sleep(2)

        # read register
        file = "res/diff.txt"
        print("read file " + file)
        register = self.readRegister(file)

        # disable outputs
        self.gpio.setOutput(False)

        # set voltage
        # WARNING USE CONFIGURED VOLTAGE
        voltage = logic.SignalVoltage.V2P5
        self.gpio.setVoltage(voltage)

        self.gpio.setInput(0)

        # write spi config
        self.spi.writeRegister(register)

        #
        # wait for spi callback
        #
        time.sleep(6)

        for i in range(8):
            time.sleep(1)
            # poll
            print("s: {} LOL: {} LOS: {}".format(i*5, self.gpio.getLOL(), self.gpio.getLOS()))
            print("register status: " + str(self.spi.readStatus()))

        # shutdown
        print("shutdown")
        message = logic.RegisterMap().PDN
        message.val = 0x1 # powerdown
        self.spi.writeRegister(message.bytes())
        self.gpio.close()
        self.spi.close()



#
#   main code
#
test = Test()
