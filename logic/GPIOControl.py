import smbus
import time
import os
import RPi.GPIO as GPIO
import logic

#
#   Interfaces with the gpios
#   Changes the pin mode to in/out when needed
#   Call close() on program end
class GPIOControl():

    def __init__(self, callback):

        # callback for input changes
        self.GPIOChange = callback

        # init gpio subsystem
        GPIO.setmode(GPIO.BCM)

        # ignore "RuntimeWarning: This channel is already in use, continuing anyway."
        # solved with __setALTmodeToW()
        GPIO.setwarnings(False)

        # Output enable pin GPIO12
        self.OE = 12
        self.__setALTmodeToW(self.OE)
        GPIO.setup(self.OE, GPIO.OUT)
        GPIO.output(self.OE, GPIO.LOW)

        # SPI connection
        self.MOSI = 10
        self.SCLK = 11
        self.MISO = 9
        self.CS = 7

        # RESET pin
        self.RESET = 17
        self.__setALTmodeToW(self.RESET)
        GPIO.setup(self.RESET, GPIO.OUT)
        GPIO.output(self.RESET, GPIO.HIGH) # LOW activ

        # IN_SEL
        self.IN_SEL0 = 20 # input select bit 0
        self.IN_SEL1 = 21 # input select bit 1
        self.__setALTmodeToW(self.IN_SEL0)
        GPIO.setup(self.IN_SEL0, GPIO.OUT)
        GPIO.setup(self.IN_SEL1, GPIO.OUT)
        GPIO.output(self.IN_SEL0, GPIO.LOW)
        GPIO.output(self.IN_SEL1, GPIO.LOW)

        # LOL
        self.LOL = 27
        GPIO.setup(self.LOL, GPIO.IN) # LOW activ

        # LOS
        self.LOS = 22
        GPIO.setup(self.LOS, GPIO.IN) # LOW activ

        # INTR
        self.INTR = 5
        GPIO.setup(self.INTR, GPIO.IN)  # LOW activ, trigger on falling edge
        GPIO.add_event_detect(self.INTR, GPIO.FALLING, callback=self.INTR_ISR, bouncetime=50)

        # VDD selection, lsb first
        self.__setALTmodeToW(14)
        self.VDD = [14,26,19,13,6]
        self.Vout = [
            [0,0,1,0,0],    # 1.8 V
            [1,1,0,1,0],    # 2.5 V
            [1,1,0,0,1]     # 3.3 V
        ]
        for pin in self.VDD:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW) # set low for vdd=0

        # LED output codes
        self.__setALTmodeToW(15)
        self.LED = [15,18,23,24,25,16]
        for pin in self.LED:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # FMC EEPROM i2c connection
        self.SCL = 3
        self.SDA = 2
        self.DEVICE_BUS = 1

        # find device: i2cdetect -y 1
        self.DEVICE_ADDR = 0x50 # http://www.fmchub.com/faq/

    #
    #   configure GPIO with system call
    #   set to write pin --> disable alt function
    def __setALTmodeToW(self, gpio):
        os.system("pigs m {} w".format(gpio))

    #
    #   reset device using reset pin
    #   takes seconds
    def resetDevice(self):
        GPIO.output(self.RESET, GPIO.LOW)
        time.sleep(1)   # hold LOW for reset
        GPIO.output(self.RESET, GPIO.HIGH)
        time.sleep(1)   # wait for reinitialisation
        print("gpio reset finished")

    #
    #   negate read bit
    #   convert GPIO.LOw / HIGH to true / false
    def __negateInput(self, gpioState):
        if (gpioState == GPIO.LOW):
            return True
        else:
            return False

    #
    #   Read LOL status
    #
    def getLOL(self):
        return self.__negateInput(GPIO.input(self.LOL))

    #
    #   Read LOS status
    #
    def getLOS(self):
        return self.__negateInput(GPIO.input(self.LOS))

    #
    #   set input channel
    #   valid: 0 or 2
    #   for other values no input channel is activated
    def setInput(self, channel):
        bit0, bit1 = GPIO.LOW, GPIO.LOW # channel 0
        if channel == 2:
            bit0 = GPIO.HIGH
            bit1 = GPIO.LOW
        else:
            pass

        #print("gpio input channel: {} SEL: {}".format(channel, [bit0, bit1]))
        GPIO.output(self.IN_SEL0, bit0)
        GPIO.output(self.IN_SEL1, bit1)

    #
    #   Enables / disables output channels with OE_b
    #   OE is low active
    def setOutput(self, enable):
        #print("gpio oe: " + str(enable))
        GPIO.output(self.OE, GPIO.LOW if enable else GPIO.HIGH)

    #
    #   interrupt service routine
    def INTR_ISR(self, unknown):
        print("INTERRUPT")
        self.GPIOChange(self.getLOL(), self.getLOS())

    #
    #   read FMC information EEPROM
    #   TODO use FMC register
    def readEEPROM(self):
        bus = smbus.SMBus(self.DEVICE_BUS)
        #byteList = bus.read_i2c_block_data(self.DEVICE_ADDR, 0, 256)
        byteList = bus.read_byte_data(self.DEVICE_ADDR, 0)
        bus.close()
        return byte

    #
    #   set output VDD voltage
    #
    def setVoltage(self, voltage):
        vIndex = 0
        if (voltage == logic.SignalVoltage.V2P5):
            vIndex = 1
        elif (voltage == logic.SignalVoltage.V3P3):
            vIndex = 2

        #print("gpio vdd: " + str(self.Vout[vIndex]))
        for i in range(len(self.VDD)):
            if self.Vout[vIndex][i] == 1:
                GPIO.output(self.VDD[i], GPIO.HIGH)
            else:
                GPIO.output(self.VDD[i], GPIO.LOW)

    #
    #   set LED state
    #   indices 1...6
    def setLed(self, index, on):
        if index > 6 or index < 1:
            return
        if on == True:
            GPIO.output(self.LED[index-1], GPIO.HIGH)
        else:
            GPIO.output(self.LED[index-1], GPIO.LOW)

    #
    #   enable led on corresponding channel
    #
    def illumChannel(self, conf):
        # LED 2 + 3 on channel 0
        self.setLed(2, conf.channels[0].enabled)
        self.setLed(3, conf.channels[0].enabled)

        # LED 4 + 5 on channel 1
        self.setLed(4, conf.channels[1].enabled)
        self.setLed(5, conf.channels[1].enabled)

        # LED 1 on input channel
        self.setLed(1, (any(map(lambda a : (a.enabled and a.index == 0), conf.inputs))))

    #
    #   close
    #   return al GPIOs to default values
    def close(self):
        GPIO.cleanup()

#
#   Test code when started as stand-alone script
#
if __name__ == "__main__":
    control = GPIOControl(None)
    print(control.getLOL())
    control.setVoltage(logic.SignalVoltage.V2P5)
    print(control.getLOL())
