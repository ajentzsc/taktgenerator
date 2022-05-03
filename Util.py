import logic.Constants as Constants
import logic
import numpy as np
from threading import Timer

#
#   Collection of multiple utility functions
#   Used from different classes, always without context (static)
#

#
#   Timer run code repeatly
#   Used in worker
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

#
#   Style text with HTML tags
#
def styleText(text, size=20, bold=False, color="black"):
    start = ""
    end = ""
    if bold:
        start = start + "<b>"
        end = "</b>" + end

    start = start + "<font font-size=\"{}px\"; color=\"{}\">".format(size, color)
    end = "</font>" + end
    return start + text.replace("\n", "<br>") + end


#
#   Prints the lock-status to string
#   uses information from "Status" class
def printLocked(conf, status):

    if any(map(lambda i: i.enabled, conf.inputs)):
        if all(map(lambda c: not c.enabled, conf.channels)):
            # not output channel configured
            return "No output configured"

        # at least one input channel
        text = ""
        if status.lol:
            # los of lock
            text = text + styleText("NO LOCK", size=30, bold=True, color="red") + "<br>"
        else:
            # locked
            text = text + styleText("LOCKED", size=30, bold=True, color="green") + "<br>"

        for ch in range(2):
            # per channel input information
            text = text + "In{}: ".format(ch*2)
            if status.input == ch*2 and not status.lol:
                text = text + styleText("LOCK", color="green") + "<br>" # locked to channel
            else:
                # not locked to this channel
                if status.los[ch*2]:
                    text = text + "No signal" + "<br>"
                elif conf.inputs[ch].enabled:
                    text = text + "Signal" + "<br>"
                else:
                    text = text + "off" + "<br>"
        return text
    else:
        return "No input configured"


#   pretty print frequency
#   returns string pair:
#   ( number, unit )
def printFreq(freq):
    if (freq % 1) == 0:
        # integer
        if freq > 100000:
            return ("{:7}".format(freq/1000000), Constants.MHZ)
        if freq > 100:
            return ("{:7}".format(freq/1000), Constants.KHZ)
        else:
            return ("{:7}".format(freq), Constants.HZ)
    else:
        # float
        if freq > 100000:
            return ("{:7.4f}".format(freq/1000000), Constants.MHZ)
        if freq > 100:
            return ("{:7.4f}".format(freq/1000), Constants.KHZ)
        else:
            return ("{:7.4f}".format(freq), Constants.HZ)


#
#   pretty print output format
#
def printFormat(conf, index):
    sig = conf.channels[index].signal
    out = sig.type + "\n"
    if (sig.type == logic.SignalType.LVCMOS_INPHASE or
        sig.type == logic.SignalType.LVCMOS_COMPL):
        out = out + "volt: " + conf.vddo + "\n"
        out = out + "term: " + Constants.TERM_OPTIONS[list(logic.SignalVoltage)
            .index(conf.vddo)][sig.impedance]
    #out = out + sig.stopHigh
    return out


#
#   Calculates efficiently the largest common multiple
#   Scales float numbers up to ints and uses the numpy lcm
def floatLCMNP(values):
    if len(values) == 1:
        return values[0]
    power = max(map(lambda v: abs(str(v)[::-1].find('.')), values))
    ints = [int(v*10**power) for v in values]
    return float(np.lcm.reduce(ints).item())/10**power


#
#   Calculates the gcd of two numbers with a
#   certain maximum error (for floats)
def floatGcd(a,b):
    r = 0
    while (a%b > logic.Constants.GCD_INPUT_ERROR):
        r = a%b
        a=b
        b=r

    return b
