#!/bin/python3
import logic
import numpy as np
import math
import Util

QUIET=False

#
#   This script is a collection of methods to calculate the channel divider
#   for output clocks and synchronizing to input clocks
#   From the UI just "calcDivider()" is called, which calculates
#   the dividers / factors matching to this configuration




#   Finds the internal frequency used to generate all output clocks
#   calculate common divider values
#
# find lowest common multiplier of all
# MN/MD*5*Fin/P=Fvco
def findFPLL(conf, frequencies):
    # active channels
    lcm = Util.floatLCMNP(frequencies)
    if not QUIET: print("lcm: " + str(lcm))

    targetFvco = 0
    # calculate M numerator and M denumerator
    if (lcm <= float(logic.Constants.MAX_PLL_F)):
        # maximum pll frequency not exceeded
        # calculate MN / MD to get lcm as pll frequency
        if not QUIET: print("maximum pll frequency not exceeded")

        targetFvco = lcm
    else:
        # maximum pll frequency exceeded
        # use maximum output frequency foutMax
        if not QUIET: print("maximum pll frequency exceeded")
        targetFvco = max(frequencies)

    # set Fvco to the biggest possible multiple of targetFvco
    conf.Mxaxb_N = math.floor(logic.Constants.MAX_PLL_F/targetFvco)*targetFvco
    conf.Mxaxb_D = logic.Constants.EXTERNAL_REF_FREQ
    conf.fvco = conf.Mxaxb_N
    print("conf.fvco old = " + str(conf.fvco))

    if conf.fvco < logic.Constants.MAX_PLL_F*0.95:
        # to low Fvco not working (example: targetFvco = 7.2GHz, ch3=720MHz, ch2=50MHz)
        # default use f_vco = 720MHz
        # --> use broken factor to fix (here 7200000000 + 7 * 2^-3 * 7200000000)
        diff = logic.Constants.MAX_PLL_F*0.95 - conf.fvco    # diff to dest fvco
        diffRel = diff/conf.fvco                            # relativ to current fvco
        log = math.floor(math.log2(diffRel))-2              # log2(0.23) --> −2,1203 --> -3 find useable fraction of old fvco to get close to dest fvco
        factor = math.ceil(diff/(conf.fvco * 2**int(log)))  # get factor to multiply fraction of old fvco with
        conf.fvco = conf.fvco + factor*(conf.fvco * 2**int(log))     # 7200MHz * 7200MHz * 2^(-2) --> 7200MHz * 1.875 <-- (factor * 2^log)
        conf.Mxaxb_N = conf.fvco
        print("needed to scale fvco up for best performance")

    # print common divider settings
    if not QUIET:
        print("Mxaxb_N: " + str(conf.Mxaxb_N))
        print("Mxaxb_D: " + str(conf.Mxaxb_D))
        print("Fvco: " + str(conf.fvco))

    return conf


#
#   Calculates the per channel divider starting from the given internal
#   frequency f_vco. This function is used when the destination frequency
#   is no integer part of the f_vco
#   Finds best divider for given pll frequency and output frequency
#   Scales divider up until integer or stop <-- get maximum resolution
def findBestDivider(conf, channel):
    # print("findBestDivider for channel {}".format(channel.index))
    bestError, bestMult = 2**logic.Constants.ND_MAX_PWR, 1
    for i in range(1, 100):
        nNew = conf.fvco*i
        dNew = channel.frequency*2*i
        errorNew = abs(conf.fvco/(nNew/float(dNew))/2-channel.frequency) # R = 2
        # print("Error: {} multiplier: {}".format(errorNew, i))

        # exceeded divider bitlength
        if ((nNew >= (2**logic.Constants.NN_MAX_PWR)) or
            (dNew >= (2**logic.Constants.ND_MAX_PWR))):
            #print("Error minimization: exceeded divider bitlength")
            break

        # divider ok
        if float(errorNew) == 0.0:
            #print("Error minimization: error ok")
            break

        # new best value
        if errorNew < bestError:
            bestError = errorNew
            bestMult = i

    channel.NN = round(conf.fvco*bestMult)
    channel.ND = round(channel.frequency*2*bestMult)
    channel.R = 2.0
    if not QUIET: print("Best Error: {} multiplier: {} NN: {} ND: {} R: {}".format(bestError, bestMult, channel.NN, channel.ND, channel.R))
    channel.realFrequency = conf.fvco/(channel.NN/float(channel.ND))/channel.R
    if not QUIET: print("Channel: {} frequency: {}".format(channel.index, channel.realFrequency))
    return channel


#   problem: the N divider divedes maximum to 1/4096
#       --> so the division must be shared between N and R divider
#           this may cause (infinitly) broken N divider
#           --> scale N divider up to reach maximum resolution
#               cap the N divider at 2**Constants.NN_MAX_VAL_PWR
def capNdivider(channel):
    if ((channel.ND / channel.NN) < (1/(2**logic.Constants.NN_MAX_VAL_PWR))):
        channel.R = 2

        # half the numerator as long the MultiSynth div is smaller than 1/4096
        while ((channel.ND / channel.NN) < (1/(2**logic.Constants.NN_MAX_VAL_PWR))):
            channel.NN = channel.NN / 2
            channel.R = channel.R * 2

        # scale the divider up again to remove the possible decimal
        # after the NN divider. Keep the numbers in then allowed bitwidth
        tmpNN = channel.NN
        tmpND = channel.ND
        while ((channel.NN % 1) != 0 and
                tmpNN < 2**logic.Constants.NN_MAX_PWR and
                tmpND < 2**logic.Constants.ND_MAX_PWR):
            channel.NN = tmpNN
            channel.ND = tmpND
            tmpND = tmpND * 2
            tmpNN = tmpNN * 2

        # the register map uses integers
        channel.NN  = int(channel.NN)
        channel.ND  = int(channel.ND)
        channel.R   = int(channel.R)

    return channel


#   calc NN / ND + R divider
#   calculate per channel divider
#   dividing Fvco down to the desired channel frequency
def calcChannelDivider(conf):
    for channel in conf.channels:
        if channel.enabled:
            # channel enabled
            divider = conf.fvco/(channel.frequency*2)
            if not QUIET:
                print("Channel: {} frequency: {}".format(channel.index, channel.frequency))
                print("Divider: {}".format(divider))

            if (min((divider % 1), (-divider % 1)) > logic.Constants.FVCO_TO_MULTI_ERROR):
                if not QUIET: print("PLL frequency is not multiple of target frequency")
                channel = findBestDivider(conf, channel)
            else:
                if not QUIET: print("PLL frequency is multiple of target frequency")
                channel.NN = int(round(divider))
                channel.ND = 1
                channel.R = 2 # divide value = (R0_REG+1) x 2

            channel = capNdivider(channel)
            channel.realFrequency = conf.fvco/(channel.NN/float(channel.ND))/channel.R

        else:
            # channel disabled
            channel.NN  = 0
            channel.ND  = 0
            channel.R   = 0
            channel.realFrequency = 0.0

    return conf


#
#   Calculates MN and MD with given Phase detector frequency
#   Shifts the divider as far left as possible for maximum resolution
def calcPhaseDetectorDivider(conf):
    Ftmp = conf.Fpfd * 5

    # M divider --> Fvco = Fvco / (Fvco/Ftmp) = Fvco
    # shift left to get maximum fractional resolution
    shift = 1
    for i in range(logic.Constants.MN_MAX_PWR):
        if (
            ((math.ceil(conf.fvco) << shift) > 2**logic.Constants.MN_MAX_PWR) or
            ((math.ceil(Ftmp) << shift) > 2**logic.Constants.MD_MAX_PWR)
            ):
            break   # width exceeded
        else:
            shift = shift + 1

    shift = shift - 1   # revert last step
    conf.MN = int(conf.fvco * 2**shift)
    conf.MD = int(Ftmp * 2**shift)
    return conf


#
#   Single input calculation
#   In case of just one input clock the phase detector frequency is set
#   to F_PFD_MAX --> 2 MHz
def inputConfigurationSingle(conf, index):
    # P divider --> Fpfd = Fin / (Fin/Fpfd) = Fpfd
    conf.inputs[index].PN = math.ceil(conf.inputs[index].frequency / logic.Constants.F_PFD_MAX)
    conf.inputs[index].PD = 1

    # calculate new Fpfd
    conf.Fpfd = conf.inputs[index].frequency / float(conf.inputs[index].PN)
    # multiply by hardware feedback divider
    conf = calcPhaseDetectorDivider(conf)

    if not QUIET:
        print("InputChannel {} PN {}, PD {}, MN {}, MD {}, Fpfd {}".format(
            index, conf.inputs[index].PN, conf.inputs[index].PD, conf.MN, conf.MD, conf.Fpfd))
    return conf


#
#   calculate input divider for locking
#   on input clocks
#   this implementation only uses integer P divider
#   Example:
#   Fin = 5 MHz                     # input frequency
#   P = ceil(Fin/Fpfd_max) = 3      # maximum 2MHz Fpfd
#   Fpfd = Fin/P = 1.6666666MHz     # phase detector frequency
#   Fpfd * 5 * M = Fvco     (the 5 is given) # pll frequency
#   --> set P + find M
def inputConfigurationMulti(conf):
    # no input?
    if not any(map(lambda a: a.enabled, conf.inputs)):
        conf.MN, conf.MD = 0, 0
        for input in conf.inputs:
            input.PN, input.PD = 0, 0
        return conf

    # problem: two input clocks must be divided to match one
    #   phase detector frequency
    # two inputs --> find gcd for phase detector frequency
    if conf.inputs[0].enabled and conf.inputs[1].enabled:
        # two frequencies
        gcd = Util.floatGcd(conf.inputs[0].frequency, conf.inputs[1].frequency)

        if (gcd < logic.Constants.F_PFD_MIN):
            # no valid f_pfd with integer divider possible
            print("input divider: gcd {} out of range\nfallback to use only channel 0".format(gcd))
        else:
            #
            #   Two input calculation
            # P divider --> Fpfd = Fin / (Fin/Fpfd) = Fpfd
            conf.Fpfd = gcd
            if gcd > logic.Constants.F_PFD_MAX:
                conf.Fpfd = gcd/math.ceil(gcd / logic.Constants.F_PFD_MAX)

            for input in conf.inputs:
                input.PN = round(input.frequency / conf.Fpfd)
                input.PD = 1
                if not QUIET: print("InputChannel {} PN {}, PD {}".format(input.index, input.PN, input.PD))

            conf = calcPhaseDetectorDivider(conf)
            if not QUIET: print("MN {}, MD {}, Fpfd {} Gcd {}".format(conf.MN, conf.MD, conf.Fpfd, gcd))
            return conf

    # Configure only one channel / fallback solution
    index = 1
    if conf.inputs[0].enabled: index = 0
    return inputConfigurationSingle(conf, index)




#   Main function
#   1.  calc pll frequency
#   2.  calc per output channel divider
#   3.  calc input divider + pll divider
def calcDivider(conf):
    # show used configuration
    # only active (enabled) output channels
    frequenciesF = [] # float
    for channel in conf.channels:
        if channel.enabled:
            if not QUIET: print("Channel: {} frequency: {}".format(channel.index, channel.frequency))
            frequenciesF.append(channel.frequency*2)
    if not QUIET: print("Input " + str(conf.inputs))

    # no output configured --> reset previously calculated values
    if (len(frequenciesF) == 0):
        if not QUIET: print("No channels enabled, no divider calculation")
        for channel in conf.channels:
            channel.NN  = 0
            channel.ND  = 0
            channel.R   = 0
            channel.realFrequency = 0.0
        return conf

    # find optimal pll divider for all frequencies
    conf = findFPLL(conf, frequenciesF)

    #   calculate per channel output divider
    conf = calcChannelDivider(conf)

    # calculate input configuration for locking on clocks
    conf = inputConfigurationMulti(conf)

    # finished
    errors = [abs(e.realFrequency-e.frequency) for e in conf.channels]
    if not QUIET: print("Errors: " + str(errors))
    if not QUIET: print("Conf: " + str(conf))
    return conf
