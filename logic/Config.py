import logic
from enum import Enum

#
#   This file contains all configuration related classes / enums
#   This configuration structure is used for the gui and is later
#   translated to the RegisterMap configuration using the "setRegister"
#   script

#
#   Output channel disabled state
#
class DisabledState(str, Enum):
    STOP_LOW : str = "STOP LOW"
    STOP_HIGH : str = "STOP HIGH"

#
#   Output signal type
#
class SignalType(str, Enum):
    LVPECL : str = "LVPECL"     # 2.5 / 3.3 V
    LVDS : str = "LVDS"         # 1.8 / 2.5 / 3.3 V
    HCSL : str = "HCSL"         # 1.8 / 2.5 / 3.3 V
    LVCMOS_INPHASE : str = "LVCMOS IN PHASE"     # 1.8 (31/46 Ohm) / 2.5 (24/35/43 Ohm) / 3.3 (22/30/38 Ohm)
    LVCMOS_COMPL : str = "LVCMOS COMPL"         # 1.8 (31/46 Ohm) / 2.5 (24/35/43 Ohm) / 3.3 (22/30/38 Ohm)

#
#   Possible input signal types
#
class InputFormat(str, Enum):
    STANDARD: str = "Standard Differential | Single-ended 50% (AC)"   # IN_PULSED_CMOS_EN = 0; IN_CMOS_USE1P8 = 0
    CMOS_STD: str = "Standard CMOS 50% (DC)"        # IN_PULSED_CMOS_EN = 1; IN_CMOS_USE1P8 = 1
    CMOS_PLS: str = "Pulsed CMOS (max 1MHz)(DC)"    # IN_PULSED_CMOS_EN = 1; IN_CMOS_USE1P8 = 0
    CMOS_NON: str = "Non-standart CMOS (DC)"        # IN_PULSED_CMOS_EN = 1; IN_CMOS_USE1P8 = 0

#
#   Output voltage
#
class SignalVoltage(str, Enum):
    V1P8 : str = "1.8 V" # 1.8V
    V2P5 : str = "2.5 V" # 2.5V
    V3P3 : str = "3.3 V" # 3.3V

#
#   Output signal format
#
class SignalFormat:
    type = SignalType.LVDS
    stopHigh = DisabledState.STOP_LOW
    impedance = 0   # index in constants.impedance

    def __init__(self, type, stopHigh, impedance):
        self.type = type
        self.stopHigh = stopHigh
        self.impedance = impedance

    def __str__(self):
        return "SignalFormat: type {}, stop {}, impedance {}".format(
            self.type, self.stopHigh, self.impedance
        )

#
#   output channel configuration
#
class OutChannel:
    index = 0           # hardware index
    frequency = 0.0     # selected frequency
    signal = None       # signal type configuration
    enabled = False     # enabled flag

    NN, ND, R = 0,0,0       # output channel path divider
    realFrequency = 0.0 # real calculated output frequency

    def __init__(self, index, frequency=0.0, enabled=False, signal=SignalFormat(SignalType.LVDS, DisabledState.STOP_LOW, 0)):
        self.index = index
        self.enabled = enabled
        self.frequency = frequency
        self.signal = signal

    def __str__(self):
        return "Output channel: index {}, frequency: {}, enabled {}, NN {}, ND {}, R {}, realFrequency {}, signal: {}".format(
            self.index, self.frequency, self.enabled, self.NN, self.ND, self.R, self.realFrequency, self.signal
        )

#
#   input channel configuration
#
class Input:
    index = 0           # hardware input index
    enabled = False     # is enabled
    frequency = None    # input frequency
    format = None       # input format (InputFormat)
    PN, PD = 0,0        # channel input divider

    # index -1 --> no valid input
    def __init__(self, index=-1, frequency=0.0, format=InputFormat.STANDARD):
        self.index = index
        self.frequency = frequency
        self.format = format

    def __str__(self):
        return "Input channel: index {}, format {}, frequency: {}, PN {}, PD {}".format(
            self.index, self.format, self.frequency, self.PN, self.PD
        )

#
#   holds complete input / output configuration
#
class Configuration:
    channels = []           # output channel configuration
    inputs = []              # input channel configuration
    MN, MD = 0,0            # pll divider
    Mxaxb_N, Mxaxb_D, Pxaxb = 0,0,0   # OSC divider
    fvco = 0                # current pll frequency
    Fpfd = 0                # phase detector frequency
    regMap = None           # Register addresses + values
    vddo = SignalVoltage.V1P8

    def __init__(self, channels, inputs):
        self.channels = channels
        self.inputs = inputs

    # returns true when at least one enabled channel
    def hasActiveChannel(self):
        return any(list(map(lambda ch: ch.enabled, self.channels)))

    def __str__(self):
        text = "Configuration: \n"
        for channel in self.channels:
            text = text + str(channel) + "\n"
        for input in self.inputs:
            text = text + str(input) + "\n"
        text = text + "MN {}, MD {}, PXAXB {}, fvco {}, Fpfd {}, ".format(
            self.MN, self.MD, self.Pxaxb, self.fvco, self.Fpfd
        )
        text = text + "VDDO {} Mxaxb_N {}, Mxaxb_D {}".format(
            self.vddo, self.Mxaxb_N, self.Mxaxb_D
        )
        #text = text + "\nRegister map: \n" + str(self.regMap)
        return text
