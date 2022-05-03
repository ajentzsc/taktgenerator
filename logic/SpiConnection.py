import spidev
import time
import logic
import sys

#
#   SPI connection handling class
#   Used for writing / reading
#   Handles page adressing and burst writing
class Connection:

    def __init__(self, callback):

        # UI callback
        self.callback = callback

        # chech write commands by reading back
        self.check = False

        # spi frequency
        self.freq   = 10_000_000    # 10 MHz
        self.bus    = 0 # default bus
        self.device = 1 # use CS 1

        # messages
        self.preamble   = [(0x0B24, 0xC0),(0x0B25, 0x00),(0x0540, 0x01)]    # preamble for pll changes
        self.postamble  = [(0x0540, 0x00),(0x0B24, 0xC3),(0x0B25, 0x02)]    # postamble for pll changes
        self.softReset  = [(0x001C, 0x01)]  # soft reset
        self.postamble2  = [(0x0514, 0x01), (0x001C, 0x01), (0x0540, 0x00), (0x0B24, 0xC3), (0x0B25, 0x02)]

        # commands
        self.set_adr = 0x00     # set read / write address
        self.wr_data = 0x40     # write command
        self.rd_data = 0x80     # read command
        self.wr_data_inc = 0x60 # write data and increment address command
        self.rd_data_inc = 0xA0 # read data and increment address command
        self.wr_burst = 0xE0    # burst write command

        # start spi connection
        self.spi = spidev.SpiDev(self.bus, self.device)
        self.spi.max_speed_hz = self.freq
        self.spi.mode = 0		     # CPOL = 0 & CPHA = 0
        self.spi.threewire = False	 # four wire
        self.spi.no_cs = False       # use CS
        self.spi.lsbfirst = False    # MSB first
        self.spi.open(self.bus, self.device) # /dev/spidev0.1

        # test spi connection
        print("init spi connection")
        self.__setPage(0)
        list = self.__readBytes(2,2)
        print("spi device: Si{}{}".format(hex(list[1])[2:], hex(list[0])[2:]))


    #
    #   delay between commands
    #
    def __commDelay(self):
        time.sleep(6*1/self.freq)

    #
    #   set selected register page
    #
    def __setPage(self, page):
        self.spi.writebytes([self.set_adr, 0x1])     # page register address
        self.__commDelay()
        self.spi.writebytes([self.wr_data, page])    # page number
        self.__commDelay()

        #if (self.check):
            #print("check read page " + str(page))
            #print("page: " + str(self.__readBytes(0x1, 1)))


    #
    #   Reads length bytes starting from start
    #   at current page, returns list
    def __readBytes(self, start, length):
        list = []
        received = self.spi.xfer([self.set_adr, start, self.rd_data_inc, 0x0])
        list.append(received[3])
        #print("received: " + str(received))
        self.__commDelay()

        # transfer data
        for i in range(length-1):
            received = self.spi.xfer([self.rd_data_inc, 0x0])
            list.append(received[1])
            #print("received: " + str(received))
            self.__commDelay()

        return list


    def readStatus(self):
        self.__setPage(0)
        page0 = self.__readBytes(0xD, 0x7) # read d,e,f,10,11,12,13
        self.__setPage(5)
        page5 = self.__readBytes(0x7, 0x1) # read 0x507
        res = logic.Status(page0)
        if len(page5):
            res.input = page5[0] >> 6
        return res


    #
    #   write data using burst write command
    #   [(adr,dat),(adr,dat),(adr,dat),...]
    #   all registers must be on one page!
    def __burstWrite(self, data):
        self.__setPage(data[0][0]//256)
        payload = list(map(lambda x: x[1], data))  # list only data
        payload.insert(0, self.wr_burst)    # write command in first position
        payload.insert(1, data[0][0]%256)   # set start address
        self.__commDelay()
        self.spi.writebytes2(payload) # better than writebytes() when larger than buffer # TODO error TypeError: Non-Int/Long value in arguments: 70fa7df0.
        self.__commDelay()

        # CHECK read
        if (self.check):
            print("__burstWrite payload: " + str(payload))
            print("lengths: " + str(list(map(lambda x: type(x), payload))))
            read = self.__readBytes(data[0][0]%256, len(data))
            if (len(data) != len(read)):
                print("read after write length mismatch: {} != {}".format(len(data), len(read)))
            else:
                for i in range(len(data)):
                    print("adr: {} wr: {} rd: {}".format(data[i][0], data[i][1], read[i]))


    #   write register list
    #   [(adr,dat),(adr,dat),(adr,dat),...]
    #   grouping addresses for burst write
    def __writeList(self, data):
        last = (data[0][0]-1, 0)
        list = []
        for reg in data:
            if (reg[0] == last[0]+1) and (reg[0]//256 == last[0]//256):
                # register follows last register and is on same page
                list.append(reg)
            else:
                # register doesnt follow last register or is on other page
                self.__burstWrite(list)
                list = [reg]

            # new last written register
            last = reg

        # write last registers
        self.__burstWrite(list)

    #
    #   write register map with
    #    preamble, wait, data, soft reset, postamble
    def writeRegister(self, data):
        self.__writeList(self.preamble)
        time.sleep(0.3) # 4.2 Dynamic PLL Changes --> 300ms wait
        self.__writeList(data)

        self.__writeList(self.postamble2)
        # self.__writeList(self.softReset)
        # time.sleep(0.1)
        # self.__writeList(self.postamble)
        self.callback("wrote {} register".format(len(data)))


    #
    #   close connection
    #
    def close(self):
        self.spi.close()
