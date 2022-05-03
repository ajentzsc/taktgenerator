#
#   Generic register map register class
#   Holds single value with specific length
class Reg:
    # range of addresses (index 0 --> first byte lsb, index 1 --> last byte)
    addresses = []

    # register name
    name = ""

    # R = read
    # W = write
    # S = self clearing
    type = ""

    # range of active bits
    lsb = 0
    msb = 0

    # description
    desc = ""

    # value
    # defaults to zero
    val = 0

    def bitRange(self, rangeString):
        list = rangeString.split(":")
        if len(list) == 1:
            # only one bit
            if list[0].isnumeric():
                self.lsb = int(list[0])
                self.msb = int(list[0])
            else:
                self.lsb = -1
                self.msb = -1
        else:
            # range
            self.lsb = int(list[1])
            self.msb = int(list[0])


    def __init__(self, addresses, bits, type, name, desc, val=0):
        self.addresses = addresses
        self.bitRange(bits)
        self.type = type.strip()
        self.name = name.strip()
        self.desc = desc.strip()
        self.val = val

    def listToString(self, inList, useHex=False):
        if len(inList) < 1:
            return ""
        text = ""
        if useHex:
            text = hex(inList[0])[2:]
            for element in inList[1:]:
                text = text + ", " + hex(element)[2:]
        else:
            text = str(inList[0])
            for element in inList[1:]:
                text = text + ", " + str(element)
        return text

    def fullStr(self):
        return "{} {} {} {}:{} {} {:43s}".format(
            self.name,
            self.listToString(self.addresses, True),
            self.type,
            str(self.lsb),
            str(self.msb),
            hex(self.val),
            self.desc[:43]
            )

    #
    #   write register value in bytes
    #   returns list, even when only 1 register address returned
    def bytes(self):
        if len(self.addresses) == 1:
            # mask data to bits but return bits in right register position
            diff = self.msb+1 - self.lsb
            res = ((1 << diff) - 1) & self.val
            return [(self.addresses[0], res << self.lsb)]
        else:
            # msb has highest address, lsb lowest
            byteIndex = 0
            res = []
            for byte in range(self.addresses[0], self.addresses[1]+1):
                res.append((byte, (self.val >> byteIndex*8) & 0xFF))
                byteIndex = byteIndex + 1
            return res

    def __str__(self):
        return "{:15s} {:8s} {:4s} {:>2s}:{:2s} {:16s} {:43s}".format(
            self.name[:15],
            self.listToString(self.addresses, True)[:8],
            self.type[:4],
            str(self.lsb),
            str(self.msb),
            hex(self.val)[:16],
            self.desc[:43]
            )


#
#
#   Wrapper class for per channel register
#   This is used in the following RegisterMap class to use the
#   channel register in an array-like structure
#
class ChannelWrapper():
    # Overwritten by derived class
    def __init__(self, index, offset):
        pass

    def __str__(self):
        return "".join([ (str(getattr(self, key)) +"\n") for key in list(vars(self).keys())])

    # return list of all registers
    def getRegs(self):
        regs = []
        for key in list(vars(self).keys()):
            val = getattr(self, key)
            if isinstance(val, Reg):
                regs.append(val)
        return regs

#
#   Output channel format register wrapper
#
class OutputFormatChannel(ChannelWrapper):

    def __init__(self, index, offset):
        self.index = ("OutputFormatChannel", index)
        # calculate addresses by adding the channel offset
        # Si5394 offsets: [0x0112, 0x0117, 0x0126, 0x012B]
        self.OUT_PDN         = Reg([0x00+offset], "0",    "R/W",  ("OUT"+str(index)+"_PDN"),             "Output driver 0: 0 to power up the regulator, 1 to power down the regulator. Clock outputs will be weakly pulled-low.")
        self.OUT_OE          = Reg([0x00+offset], "1",    "R/W",  ("OUT"+str(index)+"_OE"),              "Output driver 0: 0 to disable the output, 1 to enable the output")
        self.OUT_RDIV_FORCE2 = Reg([0x00+offset], "2",    "R/W",  ("OUT"+str(index)+"_RDIV_FORCE2"),     "0 R0 divider value is set by R0_REG 1 R0 divider value is forced into divide by 2")
        self.OUT_FORMAT      = Reg([0x01+offset], "2:0",  "R/W",  ("OUT"+str(index)+"_FORMAT"),          "0 Reserved 1 swing mode (normal swing) differential 2 swing mode (high swing) differential 3 Reserved 4 LVCMOS single ended 5 LVCMOS (+ pin only) 6 LVCMOS (– pin only) 7Reserved")
        self.OUT_SYNC_EN     = Reg([0x01+offset], "3",    "R/W",  ("OUT"+str(index)+"_SYNC_EN"),         "0 disable 1 enable Enable/disable synchronized (glitchless) operation. When enabled, the power down and output enables are synchronized to the outputclock.")
        self.OUT_DIS_STATE   = Reg([0x01+offset], "5:4",  "R/W",  ("OUT"+str(index)+"_DIS_STATE"),       "Determines the state of an output driver when disa- bled, selectable as 00 Disable low 01 Disable high 10 Reserved 11 Reserved")
        self.OUT_CMOS_DRV    = Reg([0x01+offset], "7:6",  "R/W",  ("OUT"+str(index)+"_CMOS_DRV"),        "LVCMOS output impedance. Selectable as CMOS1,CMOS2,CMOS3.")
        self.OUT_CM          = Reg([0x02+offset], "3:0",  "R/W",  ("OUT"+str(index)+"_CM"),              "Output common mode voltage adjustment Programmable swing mode with normal swing config: Step size=100 mV Range=0.9V to 2.3V if VDDO=3.3V Range=0.6V to 1.5V if VDDO=2.5V Range=0.5V to 0.9V if VDDO=1.8 V Programmable swing mode with high0 swing config: Step size = 100mV Range = 0.9V to 2.3V if VDDO = 3.3 V Range=0.6V to 1.5V if VDDO=2.5V Range =0.5V to 0.9 V if VDDO=1.8V LVCMOS mode: Not supp/No effect")
        self.OUT_AMPL        = Reg([0x02+offset], "6:4",  "R/W",  ("OUT" + str(index) + "_AMPL"),        "Output swing adjustment Programmable swing mode with normal swing configu- ration: Step size = 100 mV Range = 100 mVpp-se to 800 mVpp-se Programmable swing mode with high swing configura- tion: Step size = 200 mV Range = 200 mVpp-se to 1600 mVpp-se LVCMOS mode: Not supported/No effect")
        self.OUT_MUX_SEL     = Reg([0x03+offset], "1:0",  "R/W",  ("OUT" + str(index) + "_MUX_SEL"),     "Output driver 0 input mux select.This selects the source of the multisynth. 0: N0 1: N1 2: Reserved 3: Reserved 4: Reserved 5: Reserved 6: Reserved 7:Reserved")
        self.OUT_VDD_SEL_EN  = Reg([0x03+offset], "3",    "R/W",  ("OUT" + str(index) + "_VDD_SEL_EN"),  "1 = Enable OUT0_VDD_SEL")
        self.OUT_VDD_SEL     = Reg([0x03+offset], "5:4",  "R/W",  ("OUT" + str(index) + "_VDD_SEL"),     "Must be set to the VDD0 voltage. 0: 3.3 V 1: 1.8 V 2: 2.5 V 3:Reserved")
        self.OUT_INV         = Reg([0x03+offset], "7:6",  "R/W",  ("OUT" + str(index) + "_INV"),         "CLK and CLK not inverted CLK inverted CLK and CLK inverted CLK inverted")

#
#   Output channel divider register wrapper
#
class OutputDividerChannel(ChannelWrapper):

    def __init__(self, index, offset):
        self.index = ("OutputDividerChannel", index)
        # calculate addresses by adding the channel offset
        # offset addresses: 0x302, 0x030D, 0x0318, 0x0323
        self.N_NUM    = Reg([0x00+offset,0x05+offset], "43:0", "R/W",    ("N"+str(index)+"_NUM"),    "44-bit Integer Number")
        self.N_DEN    = Reg([0x06+offset,0x09+offset], "31:0", "R/W",    ("N"+str(index)+"_DEN"),    "Denominator32-bit Integer")
        self.N_UPDATE = Reg([0x0A+offset],             "0",    "S",      ("N"+str(index)+"_UPDATE"), "Set this bit to update the N0 divider.")
        self.N_FSTEPW = Reg([0x033B+6*index,0x0340+6*index],"43:0","R/W",("N"+str(index)+"_FSTEPW"),"44-bit Integer Number")
        # the "+(index//2*6)" is because of hole in RN_REG addressing after R1_REG
        self.R_REG    = Reg([0x0250+3*index+(index//2*6),0x0252+3*index+(index//2*6)],"23:0","R/W",("R"+str(index)+"_REG"),"A 24 bit integer divider. Divide value = (R0_REG+1) x 2 To set R0 = 2, set OUT0_RDIV_FORCE2 = 1, and then the R0_REG value isirrelevant.")
#
#   Input channel divider register wrapper
#
class InputDividerChannel(ChannelWrapper):

    def __init__(self, index, offset):
        self.index = ("InputDividerChannel", index)
        # calculate addresses by adding the channel offset
        self.P_NUM =        Reg([0x00+offset,0x05+offset], "47:0", "R/W", ("P" + str(index) + "_NUM"), "48-bit Integer Number")
        self.P_DEN =        Reg([0x06+offset,0x09+offset], "31:0", "R/W", ("P" + str(index) + "_DEN"), "32-bit Integer Number")
        self.P_UPDATE     = Reg([0x0230],    str(index),         "S",   ("P"+str(index)+"_UPDATE"),    "0: No update for P-divider value 1: Update P-divider value")
        self.P_FRACN_MODE = Reg([0x0231+index],    "3:0",       "R/W",  ("P"+str(index)+"_FRACN_MODE"),"PX (IN X) input divider fractional mode. Must be set to 0xB for properoperation.")
        self.P_FRAC_EN    = Reg([0x0231+index],    "4",         "R/W",  ("P"+str(index)+"_FRAC_EN"),   "PX (IN X) input divider fractional enable 0: Integer-only division. 1: Fractional (or Integer)division.")

#
#   Holds all register information for Si5394
#   Not all are needed for this usecase
#   This "RegisterMap" exists as single instance in the "configuration"
#   data structure. It is refreshed with every setRegister run
#
#
class RegisterMap:

    def __init__(self):
        #self.PAGE                          = Reg([0x0001],    "7:0",       "R/W",  "PAGE",                     "Selects one of 256 possiblepages.")
        self.PN_BASE                       = Reg([0x0002,0x0003],    "15:0",       "R",    "PN_BASE",                  "0x92Four-digit “base” part number, one nibble per digit Example: Si5392A-A-GM. The base part number (OPN) is 5392, which is stored in thisregister.")
        self.GRADE                         = Reg([0x0004],    "7:0",       "R",    "GRADE",                    "One ASCII character indicating the device speed/syn- thesis mode 0 = A, 1 = B, 2 = C, 3 = D , 4 =E 9=J, 10=K,11=L,12=M,15=Petc")
        #self.TEMP_GRADE                    = Reg([0x0009],    "7:0",       "R/W",  "TEMP_GRADE",               "Device temperature grading 0 = Industrial (–40° C to 85° C) ambientconditions")
        #self.PKG_ID                        = Reg([0x000A],    "7:0",       "R/W",  "PKG_ID",                   "Package ID 1 = 7 x 7 mm 44QFN")
        self.I2C_ADDR                      = Reg([0x000B],    "6:0",       "R/W",  "I2C_ADDR",                 "The upper 5 bits of the 7 bit I2C address. The lower 2 bits are controlled by the A1 and A0 pins. Note: This register is not bankburnable.")
        self.SYSINCAL                      = Reg([0x000C],    "0",         "R",    "SYSINCAL",                 "1 if the device iscalibrating.")
        self.LOSXAXB                       = Reg([0x000C],    "1",         "R",    "LOSXAXB",                  "1 if there is no signal at the XAXBpins.")
        self.XAXB_ERR                      = Reg([0x000C],    "3",         "R",    "XAXB_ERR",                 "1 if there is a problem locking to the XAXB inputsignal.")
        self.SMBUS_TIMEOUT                 = Reg([0x000C],    "5",         "R",    "SMBUS_TIMEOUT",            "1 if there is an SMBus timeouterror.")
        self.LOS                           = Reg([0x000D],    "3:0",       "R",    "LOS",                      "1 if the clock input is currentlyLOS")
        self.OOF                           = Reg([0x000D],    "7:4",       "R",    "OOF",                      "1 if the clock input is currentlyOOF")
        self.LOL                           = Reg([0x000E],    "1",         "R",    "LOL",                      "1 if the DSPLL is out oflock")
        self.HOLD                          = Reg([0x000E],    "5",         "R",    "HOLD",                     "1 if the DSPLL is in holdover (or freerun)")
        self.CAL_PLL                       = Reg([0x000F],    "5",         "R",    "CAL_PLL",                  "1 if the DSPLL internal calibration isbusy")
        self.SYSINCAL_FLG                  = Reg([0x0011],    "0",         "R/W",  "SYSINCAL_FLG",             "Sticky version of SYSINCAL. Write a 0 to this bit toclear.")
        self.LOSXAXB_FLG                   = Reg([0x0011],    "1",         "R/W",  "LOSXAXB_FLG",              "Sticky version of LOSXAXB. Write a 0 to this bit toclear.")
        self.XAXB_ERR_FLG                  = Reg([0x0011],    "3",         "R/W",  "XAXB_ERR_FLG",             "Sticky version of XAXB_ERR.Write a 0 to this bit toclear.")
        self.SMBUS_TIMEOUT_FLG             = Reg([0x0011],    "5",         "R/W",  "SMBUS_TIMEOUT_FLG",        "Sticky version of SMBUS_TIMEOUT. Write a 0 to this bit toclear.")
        self.LOS_FLG                       = Reg([0x0012],    "3:0",       "R/W",  "LOS_FLG",                  "1 if the clock input is LOS for the giveninput")
        self.OOF_FLG                       = Reg([0x0012],    "7:4",       "R/W",  "OOF_FLG",                  "1 if the clock input is OOF for the giveninput")
        self.LOL_FLG                       = Reg([0x0013],    "1",         "R/W",  "LOL_FLG",                  "1 if the DSPLL wasunlocked")
        self.HOLD_FLG                      = Reg([0x0013],    "5",         "R/W",  "HOLD_FLG",                 "1 if the DSPLL was in holdover or freerun")
        self.CAL_FLG_PLL                   = Reg([0x0014],    "5",         "R/W",  "CAL_FLG_PLL",              "1 if the internal calibration wasbusy")
        self.LOL_ON_HOLD                   = Reg([0x0016],    "1",         "R/W",  "LOL_ON_HOLD",              "Set byCBPro.")
        self.SYSINCAL_INTR_MSK             = Reg([0x0017],    "0",         "R/W",  "SYSINCAL_INTR_MSK",        "1 to mask SYSINCAL_FLG from causing an in-terrupt")
        self.LOSXAXB_INTR_MSK              = Reg([0x0017],    "1",         "R/W",  "LOSXAXB_INTR_MSK",         "1 to mask the LOSXAXB_FLG from causing aninterrupt")
        self.SMB_TMOUT_INTR_MSK            = Reg([0x0017],    "5",         "R/W",  "SMB_TMOUT_INTR_MSK",       "1 to mask SMBUS_TIMEOUT_FLG from the in-terrupt")
        self.RESERVED_STATUSA              = Reg([0x0017],    "6",         "R/W",  "RESERVED",                 "Factory set to 1 to mask reserved bit from caus- ing an interrupt. Do not clear thisbit.", 1)
        self.RESERVED_STATUSB              = Reg([0x0017],    "7",         "R/W",  "RESERVED",                 "Factory set to 1 to mask reserved bit from caus- ing an interrupt. Do not clear thisbit.", 1)
        self.LOS_INTR_MSK                  = Reg([0x0018],    "3:0",       "R/W",  "LOS_INTR_MSK",             "1 to mask the clock input LOSflag")
        self.OOF_INTR_MSK                  = Reg([0x0018],    "7:4",       "R/W",  "OOF_INTR_MSK",             "1 to mask the clock input OOFflag")
        self.LOL_INTR_MSK                  = Reg([0x0019],    "1",         "R/W",  "LOL_INTR_MSK",             "1 to mask the clock input LOLflag")
        self.HOLD_INTR_MSK                 = Reg([0x0019],    "5",         "R/W",  "HOLD_INTR_MSK",            "1 to mask the holdoverflag")
        self.CAL_INTR_MSK                  = Reg([0x001A],    "5",         "R/W",  "CAL_INTR_MSK",             "MSK1 to mask the DSPLL internal calibration busyflag")
        self.SOFT_RST_ALL                  = Reg([0x001C],    "0",         "S",    "SOFT_RST_ALL",             "1 Initialize and calibrates the entire device 0 Noeffect")
        self.SOFT_RST                      = Reg([0x001C],    "2",         "S",    "SOFT_RST",                 "1 Initialize outer loop 0 Noeffect")
        self.FINC                          = Reg([0x001D],    "0",         "S",    "FINC",                     "1 a rising edge will cause the selected MultiSynth to increment the output frequency by the Nx_FSTEPW pa- rameter. See registers 0x0339-0x0353 0 Noeffect")
        self.FDEC                          = Reg([0x001D],    "1",         "S",    "FDEC",                     "1 a rising edge will cause the selected MultiSynth to decrement the output frequency by the Nx_FSTEPW parameter. See registers 0x0339-0x03530 Noeffect")
        self.PDN                           = Reg([0x001E],    "0",         "R/W",  "PDN",                      "1 to put the device into low powermode")
        # self.HARD_RST                      = Reg([0x001E],    "1",         "R/W",  "HARD_RST",                 "1 causes hard reset. The same as power up except that the serial port access is not held at reset. 0 Noreset")
        # self.SYNC                          = Reg([0x001E],    "2",         "S",    "SYNC",                     "1 to reset all output R dividers to the samestate.")
        self.SPI_3WIRE                     = Reg([0x002B],    "3",         "R/W",  "SPI_3WIRE",                "0 for 4-wire SPI, 1 for 3-wireSPI")
        self.AUTO_NDIV_UPDATE              = Reg([0x002B],    "5",        "R/W",  "AUTO_NDIV_UPDATE",           "")
        self.LOS_EN                        = Reg([0x002C],    "3:0",      "R/W",  "LOS_EN",                   "1 to enable LOS for a clock input; 0 fordisable")
        self.LOSXAXB_DIS                   = Reg([0x002C],    "4",        "R/W",  "LOSXAXB_DIS",              "Enable LOS detection on the XAXB inputs. 0: Enable LOS Detection (default) 1: Disable LOSDetection")
        self.LOS0_VAL_TIME                 = Reg([0x002D],    "1:0",      "R/W",  "LOS0_VAL_TIME",            "Clock Input 0 0 for 2 msec 1 for 100 msec 2 for 200 msec 3 for onesecond")
        self.LOS1_VAL_TIME                 = Reg([0x002D],    "3:2",      "R/W",  "LOS1_VAL_TIME",            "Clock Input 1, same asabove")
        self.LOS2_VAL_TIME                 = Reg([0x002D],    "5:4",      "R/W",  "LOS2_VAL_TIME",            "Clock Input 2, same asabove")
        self.LOS3_VAL_TIME                 = Reg([0x002D],    "7:6",      "R/W",  "LOS3_VAL_TIME",            "Clock Input 3, same asabove")
        self.LOS0_TRG_THR                  = Reg([0x002E,0x002F],    "15:0",      "R/W",  "LOS0_TRG_THR",     "16-bit ThresholdValue")
        self.LOS1_TRG_THR                  = Reg([0x0030,0x0031],    "15:0",      "R/W",  "LOS1_TRG_THR",     "16-bit ThresholdValue")
        self.LOS2_TRG_THR                  = Reg([0x0032,0x0033],    "15:0",      "R/W",  "LOS2_TRG_THR",     "16-bit ThresholdValue")
        self.LOS3_TRG_THR                  = Reg([0x0034,0x0035],    "15:0",      "R/W",  "LOS3_TRG_THR",     "16-bit ThresholdValue")
        self.LOS0_CLR_THR                  = Reg([0x0036,0x0037],    "15:0",      "R/W",  "LOS0_CLR_THR",     "16-bit ThresholdValue")
        self.LOS1_CLR_THR                  = Reg([0x0038,0x0039],    "15:0",      "R/W",  "LOS1_CLR_THR",     "16-bit ThresholdValue")
        self.LOS2_CLR_THR                  = Reg([0x003A,0x003B],    "15:0",      "R/W",  "LOS2_CLR_THR",     "16-bit ThresholdValue")
        self.LOS3_CLR_THR                  = Reg([0x003C,0x003D],    "15:0",      "R/W",  "LOS3_CLR_THR",     "16-bit ThresholdValue")
        self.LOS_MIN_PERIOD_EN             = Reg([0x003E],    "7:4",      "R/W",  "LOS_MIN_PERIOD_EN",        "Set byCBPro")
        self.OOF_EN                        = Reg([0x003F],    "3:0",      "R/W",  "OOF_EN",                   "1 to enable, 0 todisable")
        self.FAST_OOF_EN                   = Reg([0x003F],    "7:4",      "R/W",  "FAST_OOF_EN",              "1 to enable, 0 todisable")
        self.OOF_REF_SEL                   = Reg([0x0040],    "2:0",      "R/W",  "OOF_REF_SEL",              "0 for CLKIN0 1 for CLKIN1 2 for CLKIN2 3 for CLKIN3 4 forXAXB")
        self.OOF0_DIV_SEL                  = Reg([0x0041],    "4:0",      "R/W",  "OOF0_DIV_SEL",             "Sets a divider for the OOF circuitry for each input clock 0,1,2,3. The divider value is 2OOFx_DIV_SEL. CBPro sets thesedividers.")
        self.OOF1_DIV_SEL                  = Reg([0x0042],    "4:0",      "R/W",  "OOF1_DIV_SEL",              "")
        self.OOF2_DIV_SEL                  = Reg([0x0043],    "4:0",      "R/W",  "OOF2_DIV_SEL",              "")
        self.OOF3_DIV_SEL                  = Reg([0x0044],    "4:0",      "R/W",  "OOF3_DIV_SEL",              "")
        self.OOFXO_DIV_SEL                 = Reg([0x0045],    "4:0",      "R/W",  "OOFXO_DIV_SEL",            "XO_DIV_SEL")
        self.OOF0_SET_THR                  = Reg([0x0046],    "7:0",      "R/W",  "OOF0_SET_THR",             "OOF Set threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF1_SET_THR                  = Reg([0x0047],    "7:0",      "R/W",  "OOF1_SET_THR",             "OOF Set threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF2_SET_THR                  = Reg([0x0048],    "7:0",      "R/W",  "OOF2_SET_THR",             "OOF Set threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF3_SET_THR                  = Reg([0x0049],    "7:0",      "R/W",  "OOF3_SET_THR",             "OOF Set threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF0_CLR_THR                  = Reg([0x004A],    "7:0",      "R/W",  "OOF0_CLR_THR",             "OOF Clear threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF1_CLR_THR                  = Reg([0x004B],    "7:0",      "R/W",  "OOF1_CLR_THR",             "OOF Clear threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF2_CLR_THR                  = Reg([0x004C],    "7:0",      "R/W",  "OOF2_CLR_THR",             "OOF Clear threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF3_CLR_THR                  = Reg([0x004D],    "7:0",      "R/W",  "OOF3_CLR_THR",             "OOF Clear threshold. Range is up to ±500 ppm in steps of 1/16ppm.")
        self.OOF0_DET_WIN_SEL              = Reg([0x004E],    "2:0",      "R/W",  "OOF0_DETWIN_SEL",          "Values calculated byCBPro")
        self.OOF1_DET_WIN_SEL              = Reg([0x004E],    "6:4",      "R/W",  "OOF1_DETWIN_SEL","")
        self.OOF2_DET_WIN_SEL              = Reg([0x004F],    "2:0",      "R/W",  "OOF2_DETWIN_SEL","")
        self.OOF3_DET_WIN_SEL              = Reg([0x004F],    "6:4",      "R/W",  "OOF3_DETWIN_SEL","")
        self.OOF_ON_LOS                    = Reg([0x0050],    "3:0",      "R/W",  "OOF_ON_LOS",               "Set byCBPro")
        self.FAST_OOF0_SET_THR             = Reg([0x0051],    "3:0",      "R/W",  "FAST_OOF0_SET_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF1_SET_THR             = Reg([0x0052],    "3:0",      "R/W",  "FAST_OOF1_SET_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF2_SET_THR             = Reg([0x0053],    "3:0",      "R/W",  "FAST_OOF2_SET_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF3_SET_THR             = Reg([0x0054],    "3:0",      "R/W",  "FAST_OOF3_SET_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF0_CLR_THR             = Reg([0x0055],    "3:0",      "R/W",   "FAST_OOF0_CLR_THR",       "(1+ value) x 1000ppm")
        self.FAST_OOF1_CLR_THR             = Reg([0x0056],    "3:0",      "R/W",  "FAST_OOF1_CLR_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF2_CLR_THR             = Reg([0x0057],    "3:0",      "R/W",  "FAST_OOF2_CLR_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF3_CLR_THR             = Reg([0x0058],    "3:0",      "R/W",  "FAST_OOF3_CLR_THR",        "(1+ value) x 1000ppm")
        self.FAST_OOF0_DETWIN_SEL          = Reg([0x0059],    "1:0",      "R/W",  "FAST_OOF0_DETWIN_SEL",     "Values calculated by CBPro")
        self.FAST_OOF1_DETWIN_SEL          = Reg([0x0059],    "3:2",      "R/W",  "FAST_OOF1_DETWIN_SEL","")
        self.FAST_OOF2_DETWIN_SEL          = Reg([0x0059],    "5:4",      "R/W",  "FAST_OOF2_DETWIN_SEL","")
        self.FAST_OOF3_DETWIN_SEL          = Reg([0x0059],    "7:6",      "R/W",  "FAST_OOF3_DETWIN_SEL","")
        self.OOF0_RATIO_REF                = Reg([0x005A,0x005D],    "25:0",      "R/W",  "OOF0_RATIO_REF",           "Values calculated by CBPro")
        self.OOF1_RATIO_REF                = Reg([0x005E,0x0061],    "25:0",      "R/W",  "OOF1_RATIO_REF",           "Values calculated by CBPro")
        self.OOF2_RATIO_REF                = Reg([0x0062,0x0065],    "25:0",      "R/W",  "OOF2_RATIO_REF",           "Values calculated by CBPro")
        self.OOF3_RATIO_REF                = Reg([0x0066,0x0069],    "25:0",      "R/W",  "OOF3_RATIO_REF",           "Values calculated by CBPro")
        self.LOL_FST_EN                    = Reg([0x0092],    "1",         "R/W",  "LOL_FST_EN",               "Enables fast detection of LOL. A large input frequency error will quickly assert LOL when this isenabled.")
        self.LOL_FST_DETWIN_SEL            = Reg([0x0093],    "7:4",       "R/W",  "LOL_FST_DETWIN_SEL",       "Values calculated by CBPro")
        self.LOL_FST_VALWIN_SEL            = Reg([0x0095],    "3:2",       "R/W",  "LOL_FST_VALWIN_SEL",       "Values calculated by CBPro")
        self.LOL_FST_SET_THR_SEL           = Reg([0x0096],    "7:4",       "R/W",  "LOL_FST_SET_THR_SEL",      "Values calculated by CBPro")
        self.LOL_FST_CLR_THR_SEL           = Reg([0x0098],    "7:4",       "R/W",  "LOL_FST_CLR_THR_SEL",      "Values calculated by CBPro")
        self.LOL_SLOW_EN_PLL               = Reg([0x009A],    "1",         "R/W",  "LOL_SLOW_EN_PLL",          "1 to enable LOL; 0 to disableLOL.")
        self.LOL_SLW_DETWIN_SEL            = Reg([0x009B],    "7:4",       "R/W",  "LOL_SLW_DETWIN_SEL",       "Values calculated by CBPro")
        self.LOL_SLW_VALWIN_SEL            = Reg([0x009D],    "3:2",       "R/W",  "LOL_SLW_VALWIN_SEL",       "Values calculated by CBPro")
        self.LOL_SLW_SET_THR               = Reg([0x009E],    "7:4",       "R/W",  "LOL_SLW_SET_",             "THRConfigures the loss of lock set thresholds. Selectable as 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000. Values are inppm.")
        self.LOL_SLW_CLR_THR               = Reg([0x00A0],    "7:4",       "R/W",  "LOL_SLW_CLR_",             "THRConfigures the loss of lock set thresholds. Selectable as 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000. Values are inppm.")
        self.LOL_TIMER_EN                  = Reg([0x00A2],    "1",         "R/W",  "LOL_TIMER_EN",             "0 to disable 1 to enable")
        self.LOL_CLR_DELAY_DIV256          = Reg([0x00A9,0x00AC],    "28:0",       "R/W",  "LOL_CLR_DE",               "LAY_DIV256Set byCBPro.")
        # self.ACTIVE_NVM_BANK               = Reg([0x00E2],    "7:0",       "R",    "ACTIVE_NVM_BANK",          "0x03 when no NVM burn by customer 0x0F when 1 NVM bank has been burned by customer 0x3F when 2 NVM banks have been burned by customer When ACTIVE_NVM_BANK=0x3F, the last bank has already beenburned.")
        # self.NVM_WRITE                     = Reg([0x00E3],    "7:0",       "R/W",  "NVM_WRITE",                "Write 0xC7 to initiate an NVM bankburn.")
        # self.NVM_READ_BANK                 = Reg([0x00E4],    "0",         "S",    "NVM_READ_BANK",            "When set, this bit will read the NVM down into the volatilememory.")
        self.FASTLOCK_EXTEND_MASTER_DIS    = Reg([0x00E5],    "0",         "R/W",  "FASTLOCK_EXTEND_MASTER_DIS", "no documentation copied from register map")
        self.FASTLOCK_EXTEND_EN            = Reg([0x00E5],    "5",         "R/W",  "FASTLOCK_EXTEND_EN",       "Extend Fastlock bandwidth period past LOL Clear 0: Do not extend Fastlock period 1: Extend Fastlock period(default)")
        self.FASTLOCK_EXTEND               = Reg([0x00EA,0x00ED],    "28:0",       "R/W",  "FASTLOCK_EXTEND",          "29-bit value. Set by CBPro to minimize the phase transi- ents when switching the PLL bandwidth. SeeFASTLOCK_EXTEND_SCL.")
        self.SYSINCAL_INTR                 = Reg([0x00F7],    "0",         "R",    "SYSINCAL_INTR",            "Set byCBPro.")
        self.LOSXAXB_INTR                  = Reg([0x00F7],    "1",         "R",    "LOSXAXB_INTR",             "Set byCBPro.")
        self.LOSREF_INTR                   = Reg([0x00F7],    "2",         "R",    "LOSREF_INTR",              "Set byCBPro.")
        self.LOSVCO_INTR                   = Reg([0x00F7],    "4",         "R",    "LOSVCO_INTR",              "Set byCBPro.")
        self.SMBUS_TIME_O                  = Reg([0x00F7],    "5",         "R",    "SMBUS_TIME_O",             "UT_INTRSet byCBPro.")
        self.LOS_INTR                      = Reg([0x00F8],    "3:0",       "R",    "LOS_INTR",                 "Set byCBPro.")
        self.LOL_INTR                      = Reg([0x00F9],    "1",         "R",    "LOL_INTR",                 "Set byCBPro.")
        self.HOLD_INTR                     = Reg([0x00F9],    "5",         "R",    "HOLD_INTR",                "Set byCBPro.")
        self.DEVICE_READY                  = Reg([0x00FE],    "7:0",       "R",    "DEVICE_READY",             "Ready Only byte to indicate device is ready. When read data is 0x0F one can safely read/write registers. This register is repeated on every page therefore a page write is not ever required to read the DEVICE_READYstatus.")
        self.OUTALL_DISABLE_LOW            = Reg([0x0102],    "0",         "R/W",  "OUTALL_DISABLE_LOW",       "1 Pass through the output enables, 0 disables all output drivers")

        self.OUT_FORMAT = [ OutputFormatChannel(ch[0], ch[1]) for ch in [(0,0x0112), (1,0x0117), (2,0x0126), (3,0x012B)]]

        self.OUTX_ALWAYS_ON                = Reg([0x013F],    "7:0",       "R/W",  "OUTX_ALWAYS_ON",           "This setting is managed by CBPro during zero delaymode.")
        self.OUTX_ALWAYS_ON                = Reg([0x013F,0x0140],"11:0",   "R/W",  "OUTX_ALWAYS_ON","")
        self.OUT_DIS_MSK                   = Reg([0x0141],    "1",         "R/W",  "OUT_DIS_MSK","")
        self.OUT_DIS_LOL_MSK               = Reg([0x0141],    "5",         "R/W",  "OUT_DIS_LOL_MSK","")
        self.OUT_DIS_LOSXAXB_MSK           = Reg([0x0141],    "6",         "R/W",  "OUT_DIS_LOSXAXB_MSK",      "Determines if outputs are disabled during an LOSXAXB condition. 0: All outputs disabled on LOSXAXB 1: All outputs remain enabled during LOSXAXB condition")
        self.OUT_DIS_MSK_LOS_PFD           = Reg([0x0141],    "7",         "R/W",  "OUT_DIS_MSK_LOS_PFD","")
        self.OUT_DIS_MSK_LOL               = Reg([0x0142],    "1",         "R/W",  "OUT_DIS_MSK_LOL",          "0: LOL will disable all connected out- puts 1: LOL does not disable any outputs")
        self.OUT_DIS_MSK_HOLD              = Reg([0x0142],    "5",         "R/W",  "OUT_DIS_MSK_HOLD","")
        #self.OUT_PDN_ALL                   = Reg([0x0145],    "0",         "R/W",  "OUT_PDN_ALL",              "0- no effect 1- all drivers powered down")
        self.PXAXB                         = Reg([0x0206],    "1:0",       "R/W",  "PXAXB",                    "Sets the prescale divider for the input clock onXAXB.")

        self.OUT_DIVIDER = [ OutputDividerChannel(ch[0], ch[1]) for ch in [(0,0x302), (1,0x030D), (2,0x0318), (3,0x0323)]]

        self.IN_DIVIDER = [ InputDividerChannel(ch[0], ch[1]) for ch in [(0,0x0208), (1,0x0212), (2,0x021C), (3,0x0226)]]

        self.MXAXB_NUM                     = Reg([0x0235,0x023A],    "43:0",       "R/W",  "MXAXB_NUM",                "44-bit Integer Number")
        self.MXAXB_DEN                     = Reg([0x023B,0x023E],    "31:0",       "R/W",  "MXAXB_DEN",                "32-bit Integer Number")
        self.MXAXB_UPDATE                  = Reg([0x023F],    "0",         "S",    "MXAXB_UPDATE",             "Set to 1 to update the MXAXB_NUM and MXAXB_DEN values. A SOFT_RST may also be used to update thesevalues.")
        # self.DESIGN_ID0                    = Reg([0x026B],    "7:0",       "R/W",  "DESIGN_ID0",               "ASCII encoded string defined by CBPro user, with user defined space or null padding of unused characters. A user will normally include a configu- ration ID + revision ID. For example, “ULT.1A” with null character padding sets: DESIGN_ID0: 0x55 DESIGN_ID1: 0x4C DESIGN_ID2: 0x54 DESIGN_ID3: 0x2E DESIGN_ID4: 0x31 DESIGN_ID5: 0x41 DESIGN_ID6:0x 00 DESIGN_ID7:0x00")
        # self.DESIGN_ID1                    = Reg([0x026C],    "15:8",      "R/W",  "DESIGN_ID1",               "")
        # self.DESIGN_ID2                    = Reg([0x026D],    "23:16",     "R/W",  "DESIGN_ID2",               "")
        # self.DESIGN_ID3                    = Reg([0x026E],    "31:24",     "R/W",  "DESIGN_ID3",               "")
        # self.DESIGN_ID4                    = Reg([0x026F],    "39:32",     "R/W",  "DESIGN_ID4",               "")
        # self.DESIGN_ID5                    = Reg([0x0270],    "47:40",     "R/W",  "DESIGN_ID5",               "")
        # self.DESIGN_ID6                    = Reg([0x0271],    "55:48",     "R/W",  "DESIGN_ID6",               "")
        # self.DESIGN_ID7                    = Reg([0x0272],    "63:56",     "R/W",  "DESIGN_ID7",               "")
        # self.OPN_ID0                       = Reg([0x0278],    "7:0",       "R/W",  "OPN_ID0",                  "OPN unique identifier. ASCII encoded. For exam- ple, with OPN: 5392C-A12345-GM, 12345 is the OPN unique identifier, which sets: OPN_ID0: 0x31 OPN_ID1: 0x32 OPN_ID2: 0x33 OPN_ID3: 0x34 OPN_ID4:0x35")
        # self.OPN_ID1                       = Reg([0x0279],    "15:8",      "R/W",  "OPN_ID1",                  "")
        # self.OPN_ID2                       = Reg([0x027A],    "23:16",     "R/W",  "OPN_ID2",                  "")
        # self.OPN_ID3                       = Reg([0x027B],    "31:24",     "R/W",  "OPN_ID3",                  "")
        # self.OPN_ID4                       = Reg([0x027C],    "39:32",     "R/W",  "OPN_ID4",                  "")
        # self.OPN_REVISION                  = Reg([0x027D],    "7:0",       "R/W",  "OPN_REVISION",             "")
        # self.BASELINE_ID                   = Reg([0x027E],    "7:0",       "R/W",  "BASELINE_ID",              "")
        self.OOF0_TRG_THR_EXT              = Reg([0x028A],    "4:0",       "R/W",  "OOF0_TRG_THR_EXT",         "Set byCBPro.")
        self.OOF1_TRG_THR_EXT              = Reg([0x028B],    "4:0",       "R/W",  "OOF1_TRG_THR_EXT",         "Set by CBPro")
        self.OOF2_TRG_THR_EXT              = Reg([0x028C],    "4:0",       "R/W",  "OOF2_TRG_THR_EXT",         "Set by CBPro")
        self.OOF3_TRG_THR_EXT              = Reg([0x028D],    "4:0",       "R/W",  "OOF3_TRG_THR_EXT",         "Set by CBPro")
        self.OOF0_CLR_THR_EXT              = Reg([0x028E],    "4:0",       "R/W",  "OOF0_CLR_THR_EXT",         "Set byCBPro.")
        self.OOF1_CLR_THR_EXT              = Reg([0x028F],    "4:0",       "R/W",  "OOF1_CLR_THR_EXT",         "Set by CBPro")
        self.OOF2_CLR_THR_EXT              = Reg([0x0290],    "4:0",       "R/W",  "OOF2_CLR_THR_EXT",         "Set by CBPro")
        self.OOF3_CLR_THR_EXT              = Reg([0x0291],    "4:0",       "R/W",  "OOF3_CLR_THR_EXT",         "Set by CBPro")
        self.OOF_STOP_ON_LOS               = Reg([0x0292],    "3:0",       "R/W",  "OOF_STOP_ON_LOS",          "Set by CBPro")
        self.OOF_CLEAR_ON_LOS              = Reg([0x0293],    "3:0",       "R/W",  "OOF_CLEAR_ON_LOS",         "Set by CBPro")
        self.FASTLOCK_EXTEND_SCL           = Reg([0x0294],    "7:4",       "R/W",  "FASTLOCK_EXTEND_SCL",      "Scales LOLB_INT_TIM-ER_DIV256")
        self.LOL_SLW_VALWIN_SELX           = Reg([0x0296],    "1",         "R/W",  "LOL_SLW_VALWIN_SELX",      "Set by CBPro")
        self.FASTLOCK_DLY_ONSW_EN          = Reg([0x0297],    "1",         "R/W",  "FASTLOCK_DLY_ONSW_EN",     "Set byCBPro.")
        self.FASTLOCK_DLY_ONLOL_EN         = Reg([0x0299],    "1",         "R/W",  "FASTLOCK_DLY_ONLOL_EN",    "Set byCBPro.")
        self.FASTLOCK_DLY_ONLOL            = Reg([0x029D,0x029F], "19:0",         "R/W",  "FASTLOCK_DLY_ONLOL",       "Set byCBPro.")
        self.FASTLOCK_DLY_ONSW             = Reg([0x02A9,0x02AB],    "19:0",       "R/W",  "FASTLOCK_DLY_ONSW","20-bit value. Set byCBPro.")
        self.LOL_NOSIG_TIME                = Reg([0x02B7],    "3:2",       "R/W",  "LOL_NOSIG_TIME",           "Set by CBPro.")
        self.LOS_CMOS_MIN_PER_EN           = Reg([0x02BC],    "7:6",       "R/W",  "LOS_CMOS_MIN_PER_EN",      "Set by CBPro.")
        self.N_UPDATE_ALL                  = Reg([0x0338],    "1",         "S",    "N_UPDATE_ALL",             "Set this bit to update both N dividers")
        self.N_FSTEP_MSK                   = Reg([0x0339],    "4:0",       "R/W",  "N_FSTEP_MSK",              "0 to enable FINC/FDEC updates 1 to disable FINC/FDEC updates")
        self.ZDM_EN                        = Reg([0x0487],    "0",         "R/W",  "ZDM_EN",                   "0 to disable ZD mode 1 to enable ZD mode")
        self.ZDM_IN_SEL                    = Reg([0x0487],    "2:1",       "R/W",  "ZDM_IN_SEL",               "Clock input select when in ZD mode. 0 for IN0, 1 for IN1,2 for IN2, 3 reserved Note: In ZD mode the feedback clock comes into IN3")
        self.ZDM_AUTOSW_EN                 = Reg([0x0487],    "4",         "R/W",  "ZDM_AUTOSW_EN",            "Set by CBPro.")
        self.IN_ACTV                       = Reg([0x0507],    "7:6",       "R  ",  "IN_ACTV",                  "Currently selected DSPLL input clock. 0: IN0 1: IN1 2: IN2 3: IN3")
        self.BW0_PLL                       = Reg([0x0508],    "5:0",       "R/W",  "BW0_PLL",                  "PLL bandwidth parameter")
        self.BW1_PLL                       = Reg([0x0509],    "5:0",       "R/W",  "BW1_PLL",                  "PLL bandwidth parameter")
        self.BW2_PLL                       = Reg([0x050A],    "5:0",       "R/W",  "BW2_PLL",                  "PLL bandwidth parameter")
        self.BW3_PLL                       = Reg([0x050B],    "5:0",       "R/W",  "BW3_PLL",                  "PLL bandwidth parameter")
        self.BW4_PLL                       = Reg([0x050C],    "5:0",       "R/W",  "BW4_PLL",                  "PLL bandwidth parameter")
        self.BW5_PLL                       = Reg([0x050D],    "5:0",       "R/W",  "BW5_PLL",                  "PLL bandwidth parameter")
        self.FASTLOCK_BW0_PLL              = Reg([0x050E],    "5:0",       "R/W",  "FAST_BW0_PLL",             "PLL fast bandwidth parameter")
        self.FASTLOCK_BW1_PLL              = Reg([0x050F],    "5:0",       "R/W",  "FAST_BW1_PLL",             "PLL fast bandwidth parameter")
        self.FASTLOCK_BW2_PLL              = Reg([0x0510],    "5:0",       "R/W",  "FAST_BW2_PLL",             "PLL fast bandwidth parameter")
        self.FASTLOCK_BW3_PLL              = Reg([0x0511],    "5:0",       "R/W",  "FAST_BW3_PLL",             "PLL fast bandwidth parameter")
        self.FASTLOCK_BW4_PLL              = Reg([0x0512],    "5:0",       "R/W",  "FAST_BW4_PLL",             "PLL fast bandwidth parameter")
        self.FASTLOCK_BW5_PLL              = Reg([0x0513],    "5:0",       "R/W",  "FAST_BW5_PLL",             "PLL fast bandwidth parameter")
        self.BW_UPDATE_PLL                 = Reg([0x0514],    "0",         "S  ",  "BW_UPDATE_PLL",            "Must be set to 1 to update the BWx_PLL and FAST_BWx_PLL parameters")
        self.M_NUM                         = Reg([0x0515,0x051B],    "55:0",       "R/W",  "M_NUM",                    "56-bit Number")
        self.M_DEN                         = Reg([0x051C,0x051F],    "31:0",       "R/W",  "M_DEN",                    "32-bit Number")
        self.M_UPDATE                      = Reg([0x0520],    "0",         "S  ",  "M_UPDATE",                 "Set this bit to update the M divider.")
        self.M_FRAC_MODE                   = Reg([0x0521],    "3:0",       "R/W",  "M_FRAC_MODE",              "M feedback divider fractional mode. Must be set to 0xB for proper operation.")
        self.M_FRAC_EN                     = Reg([0x0521],    "4",         "R/W",  "M_FRAC_EN",                "M feedback divider fractional enable. 0: Integer-only division 1: Fractional (or integer) division - Required for DCO operation.")
        self.PLL_OUT_RATE_SEL              = Reg([0x0521],    "5",         "R/W",  "PLL_OUT_RATE_SEL",         "Must be set to 1", 1)
        self.IN_SEL_REGCTRL                = Reg([0x052A],    "0",         "R/W",  "IN_SEL_REGCTRL",           "0 for pin controlled clock selection 1 for register controlled clock selection")
        self.IN_SEL                        = Reg([0x052A],    "2:1",       "R/W",  "IN_SEL",                   "0 for IN0, 1 for IN1, 2 for IN2, 3 for IN3 (or FB_IN)")
        self.FASTLOCK_AUTO_EN              = Reg([0x052B],    "0",         "R/W",  "FASTLOCK_AUTO_EN",         "Applies only when FASTLOCK_MAN = 0 (see be- low): 0 to disable auto fast lock when the DSPLL is out of lock 1 to enable auto fast lock")
        self.FASTLOCK_MAN                  = Reg([0x052B],    "1",         "R/W",  "FASTLOCK_MAN",             "0 for normal operation (see above) 1 to force fast lock")
        self.HOLD_EN                       = Reg([0x052C],    "0",         "R/W",  "HOLD_EN",                  "Holdover enable 0: Holdover Disabled 1: Holdover Enabled (default)")
        self.EXTRA                         = Reg([0x052C],    "2:1",         "R/W",  "EXTRA",                  "needed for LOL", 0xf)
        self.HOLD_RAMP_BYP                 = Reg([0x052C],    "3",         "R/W",  "HOLD_RAMP_BYP",            "HOLD_RAMP_BYP")
        self.HOLDEXIT_BW_SEL1              = Reg([0x052C],    "4",         "R/W",  "HOLDEXIT_BW_SEL1",         "Holdover Exit Bandwidth select. Selects the exit bandwidth from Holdover when ramped exit is dis- abled (HOLD_RAMP_BYP = 1). 0: Exit Holdover using Holdover Exit or Fastlock bandwidths (default). See HOLDEXIT_BW_SEL0 (0x059B[6]) for additional information. 1: Exit Holdover using the Normal loop bandwidth")
        self.RAMP_STEP_INTERVAL            = Reg([0x052C],    "7:5",       "R/W",  "RAMP_STEP_INTERVAL",       "Time Interval of the frequency ramp steps when ramping between inputs or when exiting holdover. Calculated by CBPro based on selection.")
        self.HOLD_RAMPBYP_NOHIST           = Reg([0x052D],    "1",         "R/W",  "HOLD_RAMPBYP_NOHIST",      "Set by CBpro")
        self.HOLD_RAMPBYP_NOHIST_EXTRA     = Reg([0x052D],    "0",         "R/W",  "HOLD_RAMPBYP_NOHIST_EXTRA","Set by CBpro, not documented", 1)
        self.HOLD_HIST_LEN                 = Reg([0x052E],    "4:0",       "R/W",  "HOLD_HIST_LEN",            "5-bit value")
        self.HOLD_HIST_DELAY               = Reg([0x052F],    "4:0",       "R/W",  "HOLD_HIST_DELAY",          "")
        self.HOLD_REF_COUNT_FRC            = Reg([0x0531],    "4:0",       "R/W",  "HOLD_REF_COUNT_FRC",       "5- bit value")
        self.HOLD_15M_CYC_COUNT            = Reg([0x0532,0x0534],    "23:0",       "R/W",  "HOLD_15M_CYC_COUNT",       "Value calculated by CBPro")
        self.FORCE_HOLD                    = Reg([0x0535],    "0",         "R/W",  "FORCE_HOLD",               "0 for normal operation 1 for force holdover")
        self.CLK_SWTCH_MODE                = Reg([0x0536],    "1:0",       "R/W",  "CLK_SWTCH_MODE",           "0 = manual 1 = automatic/non-revertive 2 = automatic/revertive 3 = Reserved")
        self.HSW_EN                        = Reg([0x0536],    "2",         "R/W",  "HSW_EN",                   "0 glitchless switching mode (phase buildout turned off) 1 hitless switching mode (phase buildout turned on) Note that hitless switching is not available in zero delay mode.")
        self.IN_LOS_MSK                    = Reg([0x0537],    "3:0",       "R/W",  "IN_LOS_MSK",               "For each clock input LOS alarm: 0 to use LOS in the clock selection logic 1 to mask LOS from the clock selection logic")
        self.IN_OOF_MSK                    = Reg([0x0537],    "7:4",       "R/W",  "IN_OOF_MSK",               "For each clock input OOF alarm: 0 to use OOF in the clock selection logic 1 to mask OOF from the clock selection logic This bit is forced to 1 if precision and fast OOF are disabled on input in CBPro.")
        self.IN0_PRIORITY                  = Reg([0x0538],    "2:0",       "R/W",  "IN0_PRIORITY",             "The priority for clock input 0 is: 0 No priority 1 for priority 1 2 for priority 2 3 for priority 3 4 for priority 4 5 to 7 are reserved")
        self.IN1_PRIORITY                  = Reg([0x0538],    "6:4",       "R/W",  "IN1_PRIORITY",             "The priority for clock input 1 is: 0 No priority 1 for priority 1 2 for priority 2 3 for priority 3 4 for priority 4 5 to 7 are reserved")
        self.IN2_PRIORITY                  = Reg([0x0539],    "2:0",       "R/W",  "IN2_PRIORITY",             "The priority for clock input 2 is: 0 No priority 1 for priority 1 2 for priority 2 3 for priority 3 4 for priority 4 5 to 7 are reserved")
        self.IN3_PRIORITY                  = Reg([0x0539],    "6:4",       "R/W",  "IN3_PRIORITY",             "The priority for clock input 3 is: 0 No priority 1 for priority 1 2 for priority 2 3 for priority 3 4 for priority 4 5 to 7 are reserved")
        self.HSW_MODE                      = Reg([0x053A],    "1:0",       "R/W",  "HSW_MODE",                 "1: Default setting, do not modify 0, 2, 3: Reserved", 1)
        self.HSW_PHMEAS_CTRL               = Reg([0x053A],    "3:2",       "R/W",  "HSW_PHMEAS_CTRL",          "0: Default setting, do not modify 1, 2, 3: Reserved", 0)
        self.HSW_PHMEAS_THR                = Reg([0x053B,0x053C],    "9:0",       "R/W",  "HSW_PHMEAS_THR",           "10-bit value. Set by CBPro.")
        self.HSW_COARSE_PM_LEN             = Reg([0x053D],    "4:0",       "R/W",  "HSW_COARSE_PM_LEN",        "Set by CBPro.")
        self.HSW_COARSE_PM_DLY             = Reg([0x053E],    "4:0",       "R/W",  "HSW_COARSE_PM_DLY",        "Set by CBPro.")
        self.HOLD_HIST_VALID               = Reg([0x053F],    "1",         "R/O",  "HOLD_HIST_VALID",          "1 = there is enough historical frequency da- ta collected for valid holdover.")
        self.FASTLOCK_STATUS               = Reg([0x053F],    "2",         "R/O",  "FASTLOCK_STATUS",          "1 = PLL is in Fast Lock operation")
        self.HSW_FINE_PM_LEN               = Reg([0x0588],    "3:0",       "R/W",  "HSW_FINE_PM_LEN",          "Set by CBPro.")
        self.PFD_EN_DELAY                  = Reg([0x0589,0x058A],    "12:0",       "R/W",  "PFD_EN_DELAY",             "Set by CBPro.")
        self.HSW_MEAS_SETTLE               = Reg([0x058B,0x058D],    "19:0",       "R/W",  "HSW_MEAS_SETTLE",          "Set by CBPro.")
        self.INIT_LP_CLOSE_HO              = Reg([0x059B],    "1",         "R/W",  "INIT_LP_CLOSE_HO",         "Set by CBPro.")
        self.INIT_LP_CLOSE_HO_EXTRA        = Reg([0x059B],    "3",         "R/W",  "INIT_LP_CLOSE_HO_EXTRA", "Set by CBPro. Not documented", 1)
        self.HOLD_PRESERVE_HIST            = Reg([0x059B],    "4",         "R/W",  "HOLD_PRESERVE_HIST",       "")
        self.HOLD_FRZ_WITH_INTONLY         = Reg([0x059B],    "5",         "R/W",  "HOLD_FRZ_WITH_INTONLY",    "")
        self.HOLDEXIT_BW_SEL0              = Reg([0x059B],    "6",         "R/W",  "HOLDEXIT_BW_SEL0",         "Set by CBPro. See HOLDEXIT_BW_SEL1")
        self.HOLDEXIT_STD_BO               = Reg([0x059B],    "7",         "R/W",  "HOLDEXIT_STD_BO",          "Set by CBPro.")
        self.HOLD_RAMPBP_NOHIST            = Reg([0x059C],    "7",         "R/W",  "HOLD_RAMPBP_NOHIST",       "Set by CBPro")
        self.HOLDEXIT_ST_BO                = Reg([0x059C],    "6",         "R/W",  "HOLDEXIT_ST_BO",           "Set by CBPro")
        self.HOLDEXIT_ST_BO_EXTRA          = Reg([0x059C],    "3:2",       "R/W",  "HOLDEXIT_ST_BO_EXTRA",     "Set by CBPro, not documented")
        self.HOLDEXIT_BW0                  = Reg([0x059D],    "5:0",       "R/W",  "HOLDEXIT_BW0",             "Set by CBPro to set the PLL bandwidth when exiting holdover, works with HOL- DEXIT_BW_SEL0 and HOLD_BW_SEL1")
        self.HOLDEXIT_BW1                  = Reg([0x059E],    "5:0",       "R/W",  "HOLDEXIT_BW1",             "Set by CBPro to set the PLL bandwidth when exiting holdover, works with HOL- DEXIT_BW_SEL0 and HOLD_BW_SEL1")
        self.HOLDEXIT_BW2                  = Reg([0x059F],    "5:0",       "R/W",  "HOLDEXIT_BW2",             "Set by CBPro to set the PLL bandwidth when exiting holdover, works with HOL- DEXIT_BW_SEL0 and HOLD_BW_SEL1")
        self.HOLDEXIT_BW3                  = Reg([0x05A0],    "5:0",       "R/W",  "HOLDEXIT_BW3",             "Set by CBPro to set the PLL bandwidth when exiting holdover, works with HOL- DEXIT_BW_SEL0 and HOLD_BW_SEL1")
        self.HOLDEXIT_BW4                  = Reg([0x05A1],    "5:0",       "R/W",  "HOLDEXIT_BW4",             "Set by CBPro to set the PLL bandwidth when exiting holdover, works with HOL- DEXIT_BW_SEL0 and HOLD_BW_SEL1")
        self.HOLDEXIT_BW5                  = Reg([0x05A2],    "5:0",       "R/W",  "HOLDEXIT_BW5",             "Set by CBPro to set the PLL bandwidth when exiting holdover, works with HOL- DEXIT_BW_SEL0 and HOLD_BW_SEL1")
        self.HSW_LIMIT                     = Reg([0x05A4],    "7:0",       "R/W",  "HSW_LIMIT",                "Set by CBPro")
        self.HSW_LIMIT_ACTION              = Reg([0x05A5],    "0",         "R/W",  "HSW_LIMIT_ACTION",         "Set by CBPro")
        self.RAMP_STEP_SIZE                = Reg([0x05A6],    "2:0",       "R/W",  "RAMP_STEP_SIZE",           "Size of the frequency ramp steps when ramping between inputs or when exiting holdover. Calculated by CBPro based on selection.")
        self.RAMP_SWITCH_EN                = Reg([0x05A6],    "3",         "R/W",  "RAMP_SWITCH_EN",           "Ramp Switching Enable 0: Disable Ramp Switching 1: Enable Ramp Switching (default)")
        self.OUT_MAX_LIMIT_EN              = Reg([0x05AC],    "0",         "R/W",  "OUT_MAX_LIMIT_EN",         "Set by CBPro")
        self.HOLD_SETTLE_DET_EN            = Reg([0x05AC],    "3",         "R/W",  "HOLD_SETTLE_DET_EN",       "Set by CBPro")
        self.OUT_MAX_LIMIT_LMT             = Reg([0x05AD,0x05AE],    "15:0",       "R/W",  "OUT_MAX_LIMIT_LMT",        "Set by CBPro")
        self.HOLD_SETTLE_TARGET            = Reg([0x05B1,0x05B2],    "15:0",       "R/W",  "HOLD_SETTLE_TARGET",       "Set by CBPro")
        self.XAXB_EXTCLK_EN                = Reg([0x090E],    "1",         "R/W",  "XAXB_EXTCLK_EN",           "0 to use a crystal at the XAXB pins 1 to use an external clock source at the XAXB pins")
        self.IO_VDD_SEL                    = Reg([0x0943],    "0",         "R/W",  "IO_VDD_SEL",               "0 for 1.8 V external connections 1 for 3.3 V external connections")
        self.IN_EN                         = Reg([0x0949],    "3:0",       "R/W",  "IN_EN",                    "0: Disable and Powerdown Input Buffer. 1: Enable Input Buffer for IN3–IN0.")
        self.IN_PULSED_CMOS_EN             = Reg([0x0949],    "7:4",       "R/W",  "IN_PULSED_CMOS_EN",        "0: Standard Input Format. 1: Pulsed CMOS Input Format for IN3–IN0. See Section 5. Clock Inputs for more information.")
        self.INX_TO_PFD_EN                 = Reg([0x094A],    "3:0",       "R/W",  "INX_TO_PFD_EN",            "Value calculated in CBPro")
        self.REFCLK_HYS_SEL                = Reg([0x094E,0x094F],"11:0",   "R/W",  "REFCLK_HYS_SEL",           "Value calculated in CBPro")
        self.IN_CMOS_USE1P8                = Reg([0x094F],    "7:4",       "R/W",  "IN_CMOS_USE1P8",           "0 = selects the Pulsed CMOS input buffer mode 1 = selects the LVCMOS input buffer mode")
        self.MXAXB_INTEGER                 = Reg([0x095E],    "0",         "R/W",  "MXAXB_INTEGER",            "Set by CBPro")
        self.N_ADD_0P5                     = Reg([0x0A02],    "4:0",       "R/W",  "N_ADD_0P5",                "Value calculated in CBPro")
        self.N_CLK_TO_OUTX_EN              = Reg([0x0A03],    "4:0",       "R/W",  "N_CLK_TO_OUTX_EN",         "Routes Multisynth outputs to output driver muxes.")
        self.N_PIBYP                       = Reg([0x0A04],    "4:0",       "R/W",  "N_PIBYP",                  "Output Multisynth integer divide mode. Bit 0 for ID0, Bit 1 for ID1, etc. 0: Nx divider is fractional. 1: Nx divider is integer.")
        self.N_PDNB                        = Reg([0x0A05],    "4:0",       "R/W",  "N_PDNB",                   "Powers down the N dividers. Set to 0 to power down unused N dividers. Must set to 1 for all active N dividers. See also related registers 0x0A03 and 0x0B4A.")
        self.N0_HIGH_FREQ                  = Reg([0x0A14],    "3",         "R/W",  "N0_HIGH_FREQ",             "Set by CBPro.")
        self.N1_HIGH_FREQ                  = Reg([0x0A1A],    "3",         "R/W",  "N1_HIGH_FREQ",             "Set by CBPro.")
        self.N2_HIGH_FREQ                  = Reg([0x0A20],    "3",         "R/W",  "N2_HIGH_FREQ",             "Set by CBPro.")
        self.N3_HIGH_FREQ                  = Reg([0x0A26],    "3",         "R/W",  "N3_HIGH_FREQ",             "Set by CBPro.")
        # self.N0_PHASE_STEP                 = Reg([0x0A38],    "7:0",       "R/W",  "N0_PHASE_STEP",            "N0 step size from 1 to 255 in units of Tvco, the VCO period.")
        # self.N0_PHASE_COUNT                = Reg([0x0A39,0x0A3A],    "15:0",       "R/W",  "N0_PHASE_COUNT",           "Lower byte of number of N0 step size changes.")
        # self.N0_PHASE_INC                  = Reg([0x0A3B],    "0",         "R/W",  "N0_PHASE_INC",             "Writing a 1 initiates a phase increment.")
        # self.N0_PHASE_DEC                  = Reg([0x0A3B],    "1",         "R/W",  "N0_PHASE_DEC",             "Writing a 1 initiates a phase decrement.")
        # self.N1_PHASE_STEP                 = Reg([0x0A3C],    "7:0",       "R/W",  "N1_PHASE_STEP",            "N1 step size from 1 to 255 in units of Tvco, the VCO period.")
        # self.N1_PHASE_COUNT                = Reg([0x0A3D,0x0A3E],    "15:0",       "R/W",  "N1_PHASE_COUNT",           "Lower byte of number of N1 step size changes.")
        # self.N1_PHASE_INC                  = Reg([0x0A3F],    "0",         "R/W",  "N1_PHASE_INC",             "Writing a 1 initiates a phase increment.")
        # self.N1_PHASE_DEC                  = Reg([0x0A3F],    "1",         "R/W",  "N1_PHASE_DEC",             "Writing a 1 initiates a phase decrement.")
        # self.N2_PHASE_STEP                 = Reg([0x0A40],    "7:0",       "R/W",  "N2_PHASE_STEP",            "N1 step size from 1 to 255 in units of Tvco, the VCO period.")
        # self.N2_PHASE_COUNT                = Reg([0x0A41,0x0A42],    "15:0",       "R/W",  "N2_PHASE_COUNT",           "Lower byte of number of N2 step size changes.")
        # self.N2_PHASE_INC                  = Reg([0x0A43],    "0",         "R/W",  "N2_PHASE_INC",             "Writing a 1 initiates a phase increment.")
        # self.N2_PHASE_DEC                  = Reg([0x0A43],    "1",         "R/W",  "N2_PHASE_DEC",             "Writing a 1 initiates a phase decrement.")
        # self.N3_PHASE_STEP                 = Reg([0x0A44],    "7:0",       "R/W",  "N3_PHASE_STEP",            "N1 step size from 1 to 255 in units of Tvco, the VCO period.")
        # self.N3_PHASE_COUNT                = Reg([0x0A45,0x0A46],    "15:0",       "R/W",  "N3_PHASE_COUNT",           "Lower byte of number of N3 step size changes.")
        # self.N3_PHASE_INC                  = Reg([0x0A47],           "0",         "R/W",  "N3_PHASE_INC",             "Writing a 1 initiates a phase increment.")
        # self.N3_PHASE_DEC                  = Reg([0x0A47],           "1",         "R/W",  "N3_PHASE_DEC",             "Writing a 1 initiates a phase decrement.")
        self.N0_IODELAY_STEP               = Reg([0x0A4C],        "7:0"  , "R/W",  "N0_IODELAY_STEP", "added from CBpro register map")
        self.N0_IODELAY_COUNT              = Reg([0x0A4D,0x0A4E], "15:0" , "R/W",  "N0_IODELAY_COUNT", "added from CBpro register map")
        self.N0_IODELAY_INC                = Reg([0x0A4F], "0"           , "R/W",  "N0_IODELAY_INC", "added from CBpro register map")
        self.N0_IODELAY_DEC                = Reg([0x0A4F], "1"           , "R/W",  "N0_IODELAY_DEC", "added from CBpro register map")
        self.N1_IODELAY_STEP               = Reg([0x0A50], "7:0"         , "R/W",  "N1_IODELAY_STEP", "added from CBpro register map")
        self.N1_IODELAY_COUNT              = Reg([0x0A51,0x0A52], "15:0" , "R/W",  "N1_IODELAY_COUNT", "added from CBpro register map")
        self.N1_IODELAY_INC                = Reg([0x0A53], "0"           , "R/W",  "N1_IODELAY_INC", "added from CBpro register map")
        self.N1_IODELAY_DEC                = Reg([0x0A53], "1"           , "R/W",  "N1_IODELAY_DEC", "added from CBpro register map")
        self.N2_IODELAY_STEP               = Reg([0x0A54], "7:0"         , "R/W",  "N2_IODELAY_STEP", "added from CBpro register map")
        self.N2_IODELAY_COUNT              = Reg([0x0A55,0x0A56], "15:0" , "R/W",  "N2_IODELAY_COUNT", "added from CBpro register map")
        self.N2_IODELAY_INC                = Reg([0x0A57], "0"           , "R/W",  "N2_IODELAY_INC", "added from CBpro register map")
        self.N2_IODELAY_DEC                = Reg([0x0A57], "1"           , "R/W",  "N2_IODELAY_DEC", "added from CBpro register map")
        self.N3_IODELAY_STEP               = Reg([0x0A58], "7:0"         , "R/W",  "N3_IODELAY_STEP", "added from CBpro register map")
        self.N3_IODELAY_COUNT              = Reg([0x0A59,0x0A5A], "15:0" , "R/W",  "N3_IODELAY_COUNT", "added from CBpro register map")
        # self.SYNC_DIS_TMR                  = Reg([0x0B2E],    "6:0",       "R/W",  "SYNC_DIS_TMR",             "Controls the synchronous output disable timeout value during a hard reset.")
        # self.SYNC_DIS_TMR_EN               = Reg([0x0B2E],    "7",         "R/W",  "SYNC_DIS_TMR_EN",          "")
        self.PDIV_FRACN_CLK_DIS            = Reg([0x0B44],    "3:0",       "R/W",  "PDIV_FRACN_CLK_DIS",       "Clock disable for the fractional divide of the input P di- viders. [P3, P2, P1, P0]. Must be set to 0 if the P divider has a fractional value. 0: Enable the clock to the fractional divide part of the P divider 1: Disable the clock to the fractional divide part of the P divider")
        self.FRACN_CLK_DIS_PLL             = Reg([0x0B44],    "5",         "R/W",  "FRACN_CLK_DIS_PLL",        "Clock disable for the fractional divide of the M divider in PLLB. Must be set to 0 if this M divider has a fractional value. 0: Enable the clock to the fractional divide part of the M divider 1: Disable the clock to the fractional divide part of the M divider.")
        self.LOS_CLK_DIS                   = Reg([0x0B46],    "3:0",       "R/W",  "LOS_CLK_DIS",              "Set to 0 for normal operation.")
        self.OOF_CLK_DIS                   = Reg([0x0B47],    "4:0",       "R/W",  "OOF_CLK_DIS",              "Set to 0 for normal operation.")
        self.OOF_DIV_CLK_DIS               = Reg([0x0B48],    "4:0",       "R/W",  "OOF_DIV_CLK_DIS",          "Set to 0 for normal operation Digital OOF divider clock user disable. Bits 3:0 are for IN3,2,1,0, Bit 4 is for OOF for the XAXB input")
        self.N_CLK_DIS                     = Reg([0x0B4A],    "4:0",       "R/W",  "N_CLK_DIS",                "Disable digital clocks to N dividers. Must be set to 0 to use each N divider. See also related registers 0x0A03 and 0x0A05.")
        self.VCO_RESET_CALCODE             = Reg([0x0B57,0x0B58],    "11:0",       "R/W",  "VCO_RESET_CALCODE",        "12-bit value. Controls the VCO frequency when a reset occurs.")
        self.VAL_DIV_CTL0                  = Reg([0x0C02],    "2:0",       "R/W",  "VAL_DIV_CTL0",             "Set by CBPro")
        self.VAL_DIV_CTL1                  = Reg([0x0C02],    "4",         "R/W",  "VAL_DIV_CTL1",             "Set by CBPro")
        self.IN_CLK_VAL_PWR_UP_DIS         = Reg([0x0C03],    "3:0",       "R/W",  "IN_CLK_VAL_PWR_UP_DIS",    "Set by CBPro")
        self.IN_CLK_VAL_EN                 = Reg([0x0C07],    "0",         "R/W",  "IN_CLK_VAL_EN",            "Set by CBPro")
        self.IN_CLK_VAL_TIME               = Reg([0x0C08],    "7:0",       "R/W",  "IN_CLK_VAL_TIME",          "Set by CBPro")

    #
    #   list of all registers
    #   sorted by address
    def getOrderedRegList(self):
        regList = []
        for key in list(vars(self).keys()):
            var = getattr(self, key)
            if type(var) == Reg:
                regList.append(var)
            elif isinstance(var, list):
                # list
                for v in var:
                    if isinstance(v, ChannelWrapper):
                        # ChannelWrapper
                        regList.extend(v.getRegs())
        return sorted(regList, key=lambda reg: reg.addresses[0])

    #
    #   toString implementation
    #
    def __str__(self):
        return "".join([ (str(reg) + "\n") for reg in self.getOrderedRegList()])

    #
    #   create transfer list from register map
    #   logical or for all registers on the same address
    #   when givenRegister is given, only these registers are included
    def buildTransferList(self, givenRegister=None):

        allRegister = []
        if givenRegister == None:
            # list of all registers (duplicates in address because byte addressing)
            allRegister = self.getOrderedRegList()
        else:
            allRegister = givenRegister

        # remove read-only register
        register = filter(lambda reg: ("W" in reg.type) or ("S" in reg.type), allRegister)

        # list of all registers (duplicates in address because byte addressing)
        expandedRegister = []
        for reg in register:
            expandedRegister.extend(reg.bytes())

        # sorted by address
        sortedRegister = sorted(expandedRegister, key=lambda reg: reg[0])

        # new byte list --> no duplicate addresses
        data = []

        # initial data byte
        squashed = sortedRegister[0]

        # or for all configuration registers on same address
        for reg in sortedRegister:
            if squashed[0] == reg[0]:
                # same address -> logical or
                squashed = (reg[0] | squashed[0], reg[1] | squashed[1])
            else:
                # new address --> add byte to transfer list
                data.append(squashed)
                squashed = reg

        # add last byte
        data.append(squashed)

        # for byte in data:
        #     print("\t{{ 0x{:04X}, 0x{:02X} }},".format(byte[0], byte[1]))
        return data
