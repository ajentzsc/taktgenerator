import logic
import math

#
#   Script used to set the right register values
#   The used "RegisterMap" is initial zero for all registers (except those which
#   are set to another value in the RegisterMap class)
#   The configuration uses values copied from the CBpro results
#


# Enable / Disable these features
# when enabled: interrupt mask = 1
LOS_ENABLE = True
LOL_ENABLE = True
OOF_ENABLE = False
HOLD_ENABLE = True
CAL_ENABLE = False
HSW_ENABLE = True

#
#   deprecated
#   Calculator frequency depended coefficient of the bandwidth register
def calcBW4(Fpfd):
    # BW4 = 7   @ Fpfd = 2 MHz
    # BW4 = 15  @ Fpfd = 1 MHz
    # BW4 = 31  @ Fpfd = 0.5 MHz ...
    if Fpfd == 0.0:
        return 7
    return int(min(round((2000_000 / Fpfd) * 1.1 * 7), 63))

#
#   shifts divider to the left and returns maximum
#   shift count with out exceeding the maximum
def leftShiftMax(num, den, maxPwrNum, maxPwrDen):
    num = int(round(num))
    den = int(round(den))
    #print("leftShiftMax num {}, den {}, maxPwrNum {}, maxPwrDen {}".format(num, den, maxPwrNum, maxPwrDen))
    for i in range(min(maxPwrNum, maxPwrDen)):
        if ((num << i) > (2**maxPwrNum-1)):
            return i-1
        if ((den << i) > (2**maxPwrDen-1)):
            return i-1
    return min(maxPwrNum, maxPwrDen)-1
#
#
#   set OOF config register
#
#
def setOOF(conf):
    # 0x003F OOF Enable
    x = 0
    if (any(map(lambda a: a.enabled, conf.inputs)) and OOF_ENABLE):
        for input in conf.inputs:
            x = x | (1 << input.index*2)

    conf.regMap.OOF_EN.val = x
    conf.regMap.FAST_OOF_EN.val = x
    conf.regMap.OOF_REF_SEL.val = 4 # XAXB as OOF reference

    # 0x0041–0x0045 OOF Divider Select
    conf.regMap.OOF0_DIV_SEL.val = 9
    conf.regMap.OOF1_DIV_SEL.val = 0
    conf.regMap.OOF2_DIV_SEL.val = 9
    conf.regMap.OOF3_DIV_SEL.val = 0
    conf.regMap.OOFXO_DIV_SEL.val = 12 # CBpro

    # 0x0046–0x0049 Out of Frequency Set Threshold
    conf.regMap.OOF0_SET_THR.val = 50
    conf.regMap.OOF1_SET_THR.val = 0
    conf.regMap.OOF2_SET_THR.val = 50
    conf.regMap.OOF3_SET_THR.val = 0

    # 0x004A-0x004D Out of Frequency Clear Threshold
    conf.regMap.OOF0_CLR_THR.val = 50
    conf.regMap.OOF1_CLR_THR.val = 0
    conf.regMap.OOF2_CLR_THR.val = 50
    conf.regMap.OOF3_CLR_THR.val = 0

    # 0x004E-0x04F OOF Detection Windows
    conf.regMap.OOF0_DET_WIN_SEL.val = 5
    conf.regMap.OOF1_DET_WIN_SEL.val = 0
    conf.regMap.OOF2_DET_WIN_SEL.val = 5
    conf.regMap.OOF3_DET_WIN_SEL.val = 0
    conf.regMap.OOF_ON_LOS.val = 10  # OOF on LOS for all channels TODO

    # 0x0051-0x0054 Fast Out of Frequency Set Threshold
    conf.regMap.FAST_OOF0_SET_THR.val = 3
    conf.regMap.FAST_OOF1_SET_THR.val = 0
    conf.regMap.FAST_OOF2_SET_THR.val = 3
    conf.regMap.FAST_OOF3_SET_THR.val = 0

    # 0x0055-0x0058 Fast Out of Frequency Clear Threshold
    conf.regMap.FAST_OOF0_CLR_THR.val = 3
    conf.regMap.FAST_OOF1_CLR_THR.val = 0
    conf.regMap.FAST_OOF2_CLR_THR.val = 3
    conf.regMap.FAST_OOF3_CLR_THR.val = 0


    # 0x0059 Fast OOF Detection Window
    conf.regMap.FAST_OOF0_DETWIN_SEL.val = 1
    conf.regMap.FAST_OOF1_DETWIN_SEL.val = 0
    conf.regMap.FAST_OOF2_DETWIN_SEL.val = 1
    conf.regMap.FAST_OOF3_DETWIN_SEL.val = 0

    # OOF Ratio for Reference
    conf.regMap.OOF0_RATIO_REF.val = 12427567
    conf.regMap.OOF1_RATIO_REF.val = 0
    conf.regMap.OOF2_RATIO_REF.val = 12427567
    conf.regMap.OOF3_RATIO_REF.val = 0

    # OOFx_TRG_THR_EXT Set by CBPro.
    conf.regMap.OOF0_TRG_THR_EXT.val = 0
    conf.regMap.OOF1_TRG_THR_EXT.val = 0
    conf.regMap.OOF2_TRG_THR_EXT.val = 0
    conf.regMap.OOF3_TRG_THR_EXT.val = 0

    # OOFx_CLR_THR_EXT Set by CBPro.
    conf.regMap.OOF0_CLR_THR_EXT.val = 0
    conf.regMap.OOF1_CLR_THR_EXT.val = 0
    conf.regMap.OOF2_CLR_THR_EXT.val = 0
    conf.regMap.OOF3_CLR_THR_EXT.val = 0

    # Set by CBPro depending on active channels
    # 	{ 0x0292, 0x3F },    also sets undocumented higher bits (0x30)
    #   { 0x0293, 0x2F },    also sets undocumented higher bits (0x20)
    for channel in conf.channels:
        # if channel.enabled:
        #     conf.regMap.OOF_STOP_ON_LOS.val = conf.regMap.OOF_STOP_ON_LOS.val | (1 << channel.index)
        #     conf.regMap.OOF_CLEAR_ON_LOS.val = conf.regMap.OOF_STOP_ON_LOS.val | (1 << channel.index)

        if not OOF_ENABLE:
            # Set to 0 for normal operation. 1 disables OOF clk
            conf.regMap.OOF_CLK_DIS.val = conf.regMap.OOF_CLK_DIS.val | (1 << channel.index)
            conf.regMap.OOF_DIV_CLK_DIS.val = conf.regMap.OOF_DIV_CLK_DIS.val | (1 << channel.index)

    # TODo temp
    conf.regMap.OOF_CLK_DIS.val = 10
    conf.regMap.OOF_DIV_CLK_DIS.val = 10
    # TODo temp

    conf.regMap.OOF_STOP_ON_LOS.val     = 10 # 0xf
    conf.regMap.OOF_CLEAR_ON_LOS.val    = 10 # 0xf

    return conf

#
#
#   set LOS config register
#
#
def setLOS(conf):
    # 0x002C LOS Enable
    x = 0
    if (any(map(lambda a: a.enabled, conf.inputs)) and LOS_ENABLE):
        for input in conf.inputs:
            if input.enabled:
                x = x | (0x1 << (input.index*2))

    conf.regMap.LOS_EN.val = x
    conf.regMap.LOSXAXB_DIS.val = 0 # XAXB LOS enabled

    # input enabled
    if any(map(lambda a: a.enabled, conf.inputs)):
        # maximum 2 clock cycles (CBpro default)
        maxLOS = round(4.0*26.5)
        maxLOS = max(min(0xFFFF, maxLOS), 1) # min 1 | max 0xFFFF
        # max 16

        # minimum 0.038 clock cycles (CBpro default)
        minLOS = math.ceil(0.038*32.0)
        minLOS = max(min(0xFFFF, minLOS), 1) # min 1 | max 0xFFFF

        if list(map(lambda a: a.enabled, conf.inputs)).count(True) == 2:
            # two inputs --> larger min period
            minLOS = math.ceil(0.483*32.0)
            minLOS = max(min(0xFFFF, minLOS), 1) # min 1 | max 0xFFFF

        for input in conf.inputs:
            if input.enabled:
                # LOS Trigger Threshold
                if (input.index*2 == 0): conf.regMap.LOS0_TRG_THR.val = maxLOS
                if (input.index*2 == 1): conf.regMap.LOS1_TRG_THR.val = maxLOS
                if (input.index*2 == 2): conf.regMap.LOS2_TRG_THR.val = maxLOS
                if (input.index*2 == 3): conf.regMap.LOS3_TRG_THR.val = maxLOS

                # LOS Trigger clear Threshold
                if (input.index*2 == 0): conf.regMap.LOS0_CLR_THR.val = minLOS
                if (input.index*2 == 1): conf.regMap.LOS1_CLR_THR.val = minLOS
                if (input.index*2 == 2): conf.regMap.LOS2_CLR_THR.val = minLOS
                if (input.index*2 == 3): conf.regMap.LOS3_CLR_THR.val = minLOS

                # 0x003E LOS_MIN_PERIOD_EN
                conf.regMap.LOS_MIN_PERIOD_EN.val = conf.regMap.LOS_MIN_PERIOD_EN.val | (1 << input.index*2)

    # 0x002D Loss of Signal Requalification Value
    conf.regMap.LOS0_VAL_TIME.val = 0 # 0: 2ms
    conf.regMap.LOS1_VAL_TIME.val = 0 # 0: 2ms
    conf.regMap.LOS2_VAL_TIME.val = 0 # 0: 2ms
    conf.regMap.LOS3_VAL_TIME.val = 0 # 0: 2ms

    conf.regMap.LOS_CMOS_MIN_PER_EN.val = 0
    conf.regMap.LOS_CLK_DIS.val = 0 # Set to 0 for normal operation.
    return conf

#
#
#   set LOL configuration register
#   all in ppm
#
def setLOL(conf):
    if any(map(lambda a: a.enabled, conf.inputs)):

        conf.regMap.LOL_FST_EN.val = 1  # enable fastlock
        conf.regMap.LOL_FST_DETWIN_SEL.val = 10 # detection window CBPro
        conf.regMap.LOL_FST_VALWIN_SEL.val = 0 # detection value CBPro
        conf.regMap.LOL_FST_SET_THR_SEL.val = 9 # 3000 ppm
        conf.regMap.LOL_FST_CLR_THR_SEL.val = 7 # 300 ppm
        conf.regMap.LOL_SLOW_EN_PLL.val = 1
        conf.regMap.LOL_SLW_DETWIN_SEL.val = 6 # detection window CBPro
        conf.regMap.LOL_SLW_VALWIN_SEL.val = 2 # detection value CBPro
        conf.regMap.LOL_SLW_SET_THR.val = 5 # 30 ppm
        conf.regMap.LOL_SLW_CLR_THR.val = 3 # 3 ppm
        conf.regMap.LOL_TIMER_EN.val = 0
        conf.regMap.LOL_CLR_DELAY_DIV256.val = 0x614b

    # Fastlock Extend Scale
    conf.regMap.FASTLOCK_EXTEND_SCL.val = 0xB

    # copied from clockbuilder pro register map
    conf.regMap.FASTLOCK_EXTEND_MASTER_DIS.val = 0

    # Fastlock
    conf.regMap.FASTLOCK_EXTEND_EN.val = 0

    # TODO calculate fastlock values
    conf.regMap.FASTLOCK_EXTEND.val = 0x600a

    conf.regMap.FASTLOCK_DLY_ONSW_EN.val = 1
    conf.regMap.FASTLOCK_DLY_ONSW.val = 0x04cc
    conf.regMap.FASTLOCK_DLY_ONLOL_EN.val = 1
    conf.regMap.FASTLOCK_DLY_ONLOL.val = 0x01fa

    # Fastlock Delay on Input Switch Enable Set by CBPro.
    conf.regMap.LOL_SLW_VALWIN_SELX.val = 1

    # Sets 417 μs as time without an input to assert LOL.
    conf.regMap.LOL_NOSIG_TIME.val = 3
    # conf.regMap.LOL_LOS_REFCLK.val = [0] read only

    return conf

#
#
#   set channel output register
#   for every enabled output channel
#
def setOutputFormat(conf):
    conf.regMap.N_CLK_DIS.val = 0x10 # default clock enable

    for channel in conf.channels:
        pwrDown = 1
        if channel.enabled:
            pwrDown = 0

        conf.regMap.OUT_FORMAT[channel.index].OUT_PDN.val = pwrDown
        conf.regMap.OUT_FORMAT[channel.index].OUT_OE.val = int(channel.enabled)

        # enable clock for active channel
        conf.regMap.N_CLK_DIS.val = conf.regMap.N_CLK_DIS.val | (pwrDown << channel.index)

        # R divider == 2?
        if channel.R == 2:
            conf.regMap.OUT_FORMAT[channel.index].OUT_RDIV_FORCE2.val = 1
        else:
            conf.regMap.OUT_FORMAT[channel.index].OUT_RDIV_FORCE2.val = 0

        # set format for cmos mode
        if (channel.signal.type == logic.SignalType.LVCMOS_INPHASE or
            channel.signal.type == logic.SignalType.LVCMOS_COMPL):
            conf.regMap.OUT_FORMAT[channel.index].OUT_FORMAT.val = 4

        # finish last clock period when turning off
        conf.regMap.OUT_FORMAT[channel.index].OUT_SYNC_EN.val = 1

        if channel.signal.stopHigh == logic.DisabledState.STOP_LOW:
            conf.regMap.OUT_FORMAT[channel.index].OUT_DIS_STATE.val = 0
        else:
            conf.regMap.OUT_FORMAT[channel.index].OUT_DIS_STATE.val = 1

        # LVCMOS Output Impedance and Drive Strength Selection
        if (channel.signal.type == logic.SignalType.LVCMOS_INPHASE or
            channel.signal.type == logic.SignalType.LVCMOS_COMPL):
            conf.regMap.OUT_FORMAT[channel.index].OUT_CMOS_DRV.val = channel.signal.impedance+1


        # The common mode voltage (VCM) for the differential
        # Normal and High Swing modes is programmable
        # in 100 mV increments from 0.7 to 2.3 V
        # set to 1V
        if (channel.signal.type == logic.SignalType.LVPECL):
            # LVPECL
            conf.regMap.OUT_FORMAT[channel.index].OUT_AMPL.val = 6 # or 3 for low power
            conf.regMap.OUT_FORMAT[channel.index].OUT_CM.val = 11
            conf.regMap.OUT_FORMAT[channel.index].OUT_FORMAT.val = 1

        elif (channel.signal.type == logic.SignalType.LVDS):
            # LVDS
            if (conf.vddo == logic.SignalVoltage.V1P8):
                conf.regMap.OUT_FORMAT[channel.index].OUT_CM.val = 13
                conf.regMap.OUT_FORMAT[channel.index].OUT_AMPL.val = 3 # or 1 for low power
            elif (conf.vddo == logic.SignalVoltage.V2P5):
                conf.regMap.OUT_FORMAT[channel.index].OUT_CM.val = 11
                conf.regMap.OUT_FORMAT[channel.index].OUT_AMPL.val = 3 # or 1 for low power
            elif (conf.vddo == logic.SignalVoltage.V3P3):
                conf.regMap.OUT_FORMAT[channel.index].OUT_CM.val = 3
                conf.regMap.OUT_FORMAT[channel.index].OUT_AMPL.val = 3 # or 1 for low power

            # use normal differential
            conf.regMap.OUT_FORMAT[channel.index].OUT_FORMAT.val = 1

        elif (channel.signal.type == logic.SignalType.HCSL):
            # HCSL
            if (conf.vddo == logic.SignalVoltage.V1P8):
                conf.regMap.OUT_FORMAT[channel.index].OUT_CM.val = 13
                conf.regMap.OUT_FORMAT[channel.index].OUT_AMPL.val = 3
            else:
                conf.regMap.OUT_FORMAT[channel.index].OUT_CM.val = 11
                conf.regMap.OUT_FORMAT[channel.index].OUT_AMPL.val = 3

        # Connect this output to the corresponding MUX
        # TODO optimize routing in multiple channel configurations
        conf.regMap.OUT_FORMAT[channel.index].OUT_MUX_SEL.val = channel.index

        # These bits are set to 1 and should not be changed
        conf.regMap.OUT_FORMAT[channel.index].OUT_VDD_SEL_EN.val = 1

        # set output voltage
        if (conf.vddo == logic.SignalVoltage.V1P8):
            conf.regMap.OUT_FORMAT[channel.index].OUT_VDD_SEL.val = 1
        elif (conf.vddo == logic.SignalVoltage.V2P5):
            conf.regMap.OUT_FORMAT[channel.index].OUT_VDD_SEL.val = 2
        elif (conf.vddo == logic.SignalVoltage.V3P3):
            conf.regMap.OUT_FORMAT[channel.index].OUT_VDD_SEL.val = 0

        if (channel.signal.type == logic.SignalType.LVCMOS_INPHASE):
            conf.regMap.OUT_FORMAT[channel.index].OUT_INV.val = 0
        elif (channel.signal.type == logic.SignalType.LVCMOS_COMPL):
            conf.regMap.OUT_FORMAT[channel.index].OUT_INV.val = 1
        else:
            # do not invert polarity
            conf.regMap.OUT_FORMAT[channel.index].OUT_INV.val = 0

    return conf

#
#
#   sets the input divider for all input channels
#
#
def setInputDivider(conf):

    conf.regMap.PDIV_FRACN_CLK_DIS.val = 0xf

    if any(map(lambda a: a.enabled, conf.inputs)):

        # iterate over channel in register map
        for inChanReg in conf.regMap.IN_DIVIDER:

            # iterate over configuration channel
            for input in conf.inputs:

                if inChanReg.index[1] == (input.index*2) and input.enabled:
                    # same index as in configuration
                    # --> enable input and set divider

                    # DO NOT LEFT SHIFT LIKE THE N-DIVIDER
                    inChanReg.P_NUM.val = input.PN
                    inChanReg.P_DEN.val = input.PD
                    inChanReg.P_UPDATE.val = 1  # update
                    inChanReg.P_FRAC_EN.val = 0
                    conf.regMap.INX_TO_PFD_EN.val = conf.regMap.INX_TO_PFD_EN.val | (1 << input.index*2)

                    # one input channel configured
                    conf.regMap.IN_EN.val =  conf.regMap.IN_EN.val | (1 << input.index*2)

                    if input.PD > 1:
                        # fractional part
                        inChanReg.P_FRAC_EN.val = 1
                        conf.regMap.PDIV_FRACN_CLK_DIS.val = conf.regMap.PDIV_FRACN_CLK_DIS.val & ~(1 << input.index*2)

                        shift = leftShiftMax(
                            input.PN,
                            input.PD,
                            logic.Constants.PN_MAX_PWR,
                            logic.Constants.PD_MAX_PWR
                            )
                        inChanReg.P_NUM.val = int(round(input.PN)) << shift
                        inChanReg.P_DEN.val = int(round(input.PD)) << shift

                    # IN_PULSED_CMOS_EN
                    if (input.format == logic.Config.InputFormat.CMOS_STD or
                        input.format == logic.Config.InputFormat.CMOS_PLS or
                        input.format == logic.Config.InputFormat.CMOS_NON):
                        # set 1 to enable dc coupled CMOS input, else (default) 0
                        conf.regMap.IN_PULSED_CMOS_EN.val = conf.regMap.IN_PULSED_CMOS_EN.val | (1 << input.index*2)

                    # IN_CMOS_USE1P8
                    if (input.format == logic.Config.InputFormat.CMOS_STD or
                        input.format == logic.Config.InputFormat.STANDARD):
                        # set 1 for Standard DC-coupled CMOS mode, else (default) 0
                        conf.regMap.IN_CMOS_USE1P8.val = conf.regMap.IN_CMOS_USE1P8.val | (1 << input.index*2)

    # must be set to 0xB for proper operation
    for inChanReg in conf.regMap.IN_DIVIDER:
        inChanReg.P_FRACN_MODE.val = 0xB

    conf.regMap.REFCLK_HYS_SEL.val = 0x249
    conf.regMap.MXAXB_INTEGER.val = 0
    return conf


#
#
#   sets the output divider for all enabled output channels
#
#
def setOutputDivider(conf):
    conf.regMap.N_CLK_TO_OUTX_EN.val = 0 # Routes Multisynth outputs to output driver muxes.
    for channel in conf.channels:
        if channel.enabled:
            # channel enabled
            shift = leftShiftMax(
                channel.NN,
                channel.ND,
                logic.Constants.NN_MAX_PWR,
                logic.Constants.ND_MAX_PWR
                )
            # divide value = (R0_REG+1) x 2
            conf.regMap.OUT_DIVIDER[channel.index].R_REG.val = int((channel.R/2)-1)
            conf.regMap.OUT_DIVIDER[channel.index].N_NUM.val = int(round(channel.NN)) << shift
            conf.regMap.OUT_DIVIDER[channel.index].N_DEN.val = int(round(channel.ND)) << shift
            conf.regMap.OUT_DIVIDER[channel.index].N_UPDATE.val = 1

            # connect the Multisynth outputs to the output driver muxes
            # here: connect every used MultiSynth to the corresponding Mux
            conf.regMap.N_CLK_TO_OUTX_EN.val = (conf.regMap.N_CLK_TO_OUTX_EN.val | (1 << channel.index))

            # fractional is default
            if (channel.ND <= 1):
                # integer divider
                conf.regMap.N_PIBYP.val = conf.regMap.N_PIBYP.val | (0x1 << channel.index)

        else:
            # channel disabled
            conf.regMap.OUT_DIVIDER[channel.index].N_UPDATE.val = 0

        conf.regMap.OUT_DIVIDER[channel.index].FSTEPW = 0 # FINC not used


    return conf

#
#
#   configures the pll parameter
#   When freerun mode (no input clocks) then no Bandwidth configuration
#
def setPLLConfig(conf):
    # set input index
    if any(map(lambda a: a.enabled, conf.inputs)):
        # atleast one active input
        conf.regMap.IN_SEL.val = conf.inputs[0].index
        conf.regMap.BW_UPDATE_PLL.val = 1

        # 4KHz
        conf.regMap.BW0_PLL.val = 19
        conf.regMap.BW1_PLL.val = 39
        conf.regMap.BW2_PLL.val = 7
        conf.regMap.BW3_PLL.val = 6
        conf.regMap.BW4_PLL.val = 63
        conf.regMap.BW5_PLL.val = 3

        # 4KHz Bandwidth Fastlock
        conf.regMap.FASTLOCK_BW0_PLL.val = 19
        conf.regMap.FASTLOCK_BW1_PLL.val = 41
        conf.regMap.FASTLOCK_BW2_PLL.val = 7
        conf.regMap.FASTLOCK_BW3_PLL.val = 6
        conf.regMap.FASTLOCK_BW4_PLL.val = 63
        conf.regMap.FASTLOCK_BW5_PLL.val = 3
    else:
        # no active input
        conf.regMap.IN_SEL.val = 0

    # 0x0206 Prescale Reference Divide Ratio
    # This can only be used with external clock sources, not crystals.
    conf.regMap.PXAXB.val = 0 # prescaler 1

    # Divider configuration
    shift = leftShiftMax(
        conf.MN,
        conf.MD,
        logic.Constants.MN_MAX_PWR,
        logic.Constants.MD_MAX_PWR
        )
    conf.regMap.M_NUM.val = int(round(conf.MN)) << max(0, shift)
    conf.regMap.M_DEN.val = int(round(conf.MD)) << max(0, shift)
    conf.regMap.M_UPDATE.val = 1  # update

    # AXBX Divider configuration
    shift = leftShiftMax(
        conf.Mxaxb_N,
        conf.Mxaxb_D,
        logic.Constants.MN_MAX_PWR,
        logic.Constants.MD_MAX_PWR
        )
    # print("shift : " + str(shift))
    # print("vorher {} nachher {}".format())
    conf.regMap.MXAXB_NUM.val = int(round(conf.Mxaxb_N)) << max(0, shift)
    conf.regMap.MXAXB_DEN.val = int(round(conf.Mxaxb_D)) << max(0, shift)
    conf.regMap.MXAXB_UPDATE.val = 1
    if (conf.Mxaxb_D > 1):
        conf.regMap.MXAXB_INTEGER.val = 0
    else:
        conf.regMap.MXAXB_INTEGER.val = 1


    frac = 0.1
    if conf.MD > 0:
        frac = (conf.MN / conf.MD) % 1 # detect upscaled integer
    if (conf.MD > 1 and frac != 0.0):
        conf.regMap.FRACN_CLK_DIS_PLL.val = 0
        conf.regMap.M_FRAC_EN.val = 1 # 1: fractional division
    else:
        conf.regMap.FRACN_CLK_DIS_PLL.val = 1
        conf.regMap.M_FRAC_EN.val   = 0 # 0: Integer-only division

    conf.regMap.M_FRAC_MODE.val = 0xB # Must be set to 0xB for proper operation.
    conf.regMap.CLK_SWTCH_MODE.val  = 2 # 2 automatic/revertive, 0 manual
    return conf


#
#
#   set phase change register values
#   phase change is not used
#
def setPhaseChange(conf):
    conf.regMap.N0_PHASE_STEP.val = 0
    conf.regMap.N0_PHASE_COUNT.val = 0
    conf.regMap.N0_PHASE_INC.val = 0
    conf.regMap.N0_PHASE_DEC.val = 0

    conf.regMap.N1_PHASE_STEP.val = 0
    conf.regMap.N1_PHASE_COUNT.val = 0
    conf.regMap.N1_PHASE_INC.val = 0
    conf.regMap.N1_PHASE_DEC.val = 0

    conf.regMap.N2_PHASE_STEP.val = 0
    conf.regMap.N2_PHASE_COUNT.val = 0
    conf.regMap.N2_PHASE_INC.val = 0
    conf.regMap.N2_PHASE_DEC.val = 0

    conf.regMap.N3_PHASE_STEP.val = 0
    conf.regMap.N3_PHASE_COUNT.val = 0
    conf.regMap.N3_PHASE_INC.val = 0
    conf.regMap.N3_PHASE_DEC.val = 0

    return conf


#
#
#   set the hitless switching registers
#   and several HOLD register
#   HSW is not used, HOLD is needed for LOL clear
#
def setHSWConfig(conf):
    conf.regMap.HSW_EN.val = HSW_ENABLE # 0 glitchless switching mode
    conf.regMap.HSW_MODE.val = 1 # default setting do not modify
    conf.regMap.HSW_PHMEAS_CTRL.val = 0 # default setting do not modify
    conf.regMap.HSW_PHMEAS_THR.val = 3 # 10-bit value. Set by CBPro.
    conf.regMap.HSW_COARSE_PM_LEN.val = 4
    conf.regMap.HSW_COARSE_PM_DLY.val = 2
    conf.regMap.HSW_FINE_PM_LEN.val = 7
    conf.regMap.PFD_EN_DELAY.val = 0x18
    conf.regMap.HSW_MEAS_SETTLE.val = 9581
    conf.regMap.INIT_LP_CLOSE_HO.val = 0
    conf.regMap.HOLD_PRESERVE_HIST.val = 1
    conf.regMap.HOLD_FRZ_WITH_INTONLY.val = 1
    conf.regMap.HOLDEXIT_BW_SEL0.val = 1
    conf.regMap.HOLDEXIT_STD_BO.val = 0
    conf.regMap.HOLD_RAMPBP_NOHIST.val = 1
    conf.regMap.HOLDEXIT_ST_BO.val = 0
    conf.regMap.HOLDEXIT_BW0.val = 19
    conf.regMap.HOLDEXIT_BW1.val = 36
    conf.regMap.HOLDEXIT_BW2.val = 12
    conf.regMap.HOLDEXIT_BW3.val = 11
    conf.regMap.HOLDEXIT_BW4.val = calcBW4(conf.Fpfd)
    conf.regMap.HOLDEXIT_BW5.val = 63
    conf.regMap.HSW_LIMIT.val = 8
    conf.regMap.HSW_LIMIT_ACTION.val = 0
    conf.regMap.RAMP_STEP_SIZE.val = 3
    conf.regMap.RAMP_SWITCH_EN.val = 0
    conf.regMap.OUT_MAX_LIMIT_EN.val = 1
    conf.regMap.HOLD_SETTLE_DET_EN.val = 1
    conf.regMap.OUT_MAX_LIMIT_LMT.val = 16311
    conf.regMap.HOLD_SETTLE_TARGET.val = 668
    return conf


#
#
#   Configuration function
#
#
def setRegister(conf):
    conf.regMap = logic.RegisterMap()

    # 0x0016
    conf.regMap.LOL_ON_HOLD.val = 1

    # 0x0017 Status Flag Masks
    conf.regMap.SYSINCAL_INTR_MSK.val = 1
    conf.regMap.LOSXAXB_INTR_MSK.val = 1
    conf.regMap.SMB_TMOUT_INTR_MSK.val = 1

    # HOLD, OOF, LOL, LOS Interrupt masks
    # default: Off
    conf.regMap.LOS_INTR_MSK.val = 0xFF
    conf.regMap.OOF_INTR_MSK.val = 0xFF
    conf.regMap.LOL_INTR_MSK.val = 0x1
    conf.regMap.HOLD_INTR_MSK.val = 0x1
    conf.regMap.CAL_INTR_MSK.val = 0x1
    if any(map(lambda a: a.enabled, conf.inputs)):
        for input in conf.inputs:
            if OOF_ENABLE:
                conf.regMap.OOF_INTR_MSK.val = conf.regMap.OOF_INTR_MSK.val^(1 << input.index*2)
            if LOS_ENABLE:
                conf.regMap.LOS_INTR_MSK.val = conf.regMap.LOS_INTR_MSK.val^(1 << input.index*2)

        if LOL_ENABLE:
            conf.regMap.LOL_INTR_MSK.val = 0x0
        if HOLD_ENABLE:
            conf.regMap.HOLD_INTR_MSK.val = 0x0
        if CAL_ENABLE:
            conf.regMap.CAL_INTR_MSK.val = 0x0

    # 0x001E Power Down and Hard Reset
    # conf.regMap.PDN.val = 0
    # conf.regMap.HARD_RST.val = 0
    # conf.regMap.SYNC.val = 0

    # 0x002B SPI 3 vs 4 Wire
    conf.regMap.SPI_3WIRE.val = 0 # use 4 wire
    conf.regMap.I2C_ADDR.val  = 0x68
    conf.regMap.AUTO_NDIV_UPDATE.val = 0

    conf = setLOS(conf)
    conf = setOOF(conf)
    conf = setLOL(conf)

    # NVM
    #conf.regMap.NVM_WRITE.val = [0]
    #conf.regMap.NVM_READ_BANK.val = [0]


    # Outputs
    conf = setOutputFormat(conf)

    # 0x0102 Global OE Gating for all Clock Output Drivers
    conf.regMap.OUTALL_DISABLE_LOW.val = 1 # enable

    # 0x013F–0x0140 Zero Delay mode cbpro
    conf.regMap.OUTX_ALWAYS_ON.val = 0

    # 0x0141 Output Disable Mask for LOS XAXB
    conf.regMap.OUT_DIS_MSK.val = 0
    conf.regMap.OUT_DIS_LOL_MSK.val = 0
    conf.regMap.OUT_DIS_LOSXAXB_MSK.val = 1  # all stay on on loss
    conf.regMap.OUT_DIS_MSK_LOS_PFD.val = 0

    # 0x0142 Output Disable Loss of Lock PLL
    conf.regMap.OUT_DIS_MSK_LOL.val = 1  # LOL wont disable outputs
    conf.regMap.OUT_DIS_MSK_HOLD.val = 1

    # 0x0145 Power Down All
    # conf.regMap.OUT_PDN_ALL.val = 0

    # Inputs
    conf = setInputDivider(conf)

    # Output divider configuration
    conf = setOutputDivider(conf)
    conf.regMap.N_UPDATE_ALL.val = 0 # default to single channel update

    # STEP Stuff
    # for FINC or FDEC --> not used
    conf.regMap.N_FSTEP_MSK.val = 0x1F # disable FINC/FDEC updates
    conf.regMap.ZDM_EN.val = 0        # 0 to disable ZD mode
    conf.regMap.ZDM_IN_SEL.val = 0    # Clock input select when in ZD mode.
    conf.regMap.ZDM_AUTOSW_EN.val = 0 # ZDM_AUTOSW_EN

    # PLL divider configuration
    conf = setPLLConfig(conf)

    # 0x052A Input Clock Select
    conf.regMap.IN_SEL_REGCTRL.val = 0 # 1 for register controlled clock selection

    # 0x052B Fast Lock Control
    conf.regMap.FASTLOCK_AUTO_EN.val = 1 # 1 to enable auto fast lock
    conf.regMap.FASTLOCK_MAN.val = 0 # 0 for normal operation

    # 0x052C Holdover Exit Control
    conf.regMap.HOLD_EN.val = HOLD_ENABLE # 1: Holdover Enabled (default)
    conf.regMap.HOLD_RAMP_BYP.val = 0
    conf.regMap.HOLDEXIT_BW_SEL1.val = 0 # 0: Exit Holdover using Holdover Exit or Fastlock bandwidths (default).
    conf.regMap.RAMP_STEP_INTERVAL.val = 4 # Calculated by CBPro based on selection.
    conf.regMap.HOLD_RAMPBYP_NOHIST.val = 1 # Set by CBPro. TODO why
    conf.regMap.HOLD_HIST_LEN.val = 0x19 # (2^LEN-1)*268ns
    conf.regMap.HOLD_HIST_DELAY.val = 0x19 # (2^DELAY)*268ns
    conf.regMap.HOLD_REF_COUNT_FRC.val = 0 # 5- bit value
    conf.regMap.HOLD_15M_CYC_COUNT.val = 0x683 # Value calculated by CBPro
    conf.regMap.FORCE_HOLD.val = 0 # 0 for normal operation TODO why


    # for automatic input clock switching
    conf.regMap.IN_LOS_MSK.val = 0x0
    conf.regMap.IN_OOF_MSK.val = 0x5 # 1 to mask OOF from the clock selection logic

    for input in conf.inputs:
        if input.enabled:
            # priority 1 --> selected but lowest prio
            # priority 0 --> not selected (default)
            if ((input.index*2) == 0): conf.regMap.IN0_PRIORITY.val = 1
            if ((input.index*2) == 1): conf.regMap.IN1_PRIORITY.val = 1
            if ((input.index*2) == 2): conf.regMap.IN2_PRIORITY.val = 2
            if ((input.index*2) == 3): conf.regMap.IN3_PRIORITY.val = 1

            # 1 to mask LOS from the clock selection logic, 0 to use in logic
            # conf.regMap.IN_LOS_MSK.val = conf.regMap.IN_LOS_MSK.val & ~(1 << input.index*2)

    # hitless switching mode (not used)
    conf = setHSWConfig(conf)

    # 0x090E XAXB Configuration
    conf.regMap.XAXB_EXTCLK_EN.val = 0 # 0 to use a crystal at the XAXB pins

    # 0x0943 Control I/O Voltage Select
    conf.regMap.IO_VDD_SEL.val = 1 # raspberry 3.3v spi connection

    conf.regMap.N_ADD_0P5.val = 0 # Value calculated in CBPro

    # shift bits to match enabled dividers
    powerUpBits, bit = 0,1
    for ch in conf.channels:
        if ch.enabled:
            powerUpBits = powerUpBits | bit
        bit = bit << 1

    conf.regMap.N_PDNB.val = powerUpBits # enabled dividers

    # phase change registers
    # conf = setPhaseChange(conf)

    # Controls the synchronous output disable timeout value during a hard reset.
    # conf.regMap.SYNC_DIS_TMR.val = 0
    # conf.regMap.SYNC_DIS_TMR_EN.val = 0


    # 0x0B57-0x0B58 VCO Calcode
    conf.regMap.VCO_RESET_CALCODE.val = 240

    # use external crystal
    conf.regMap.XAXB_EXTCLK_EN.val = 1

    # Set by CBPro
    conf.regMap.VAL_DIV_CTL0.val = 0x3
    conf.regMap.VAL_DIV_CTL1.val = 0

    for input in conf.inputs:
        if input.enabled:
            conf.regMap.IN_CLK_VAL_PWR_UP_DIS.val = conf.regMap.IN_CLK_VAL_PWR_UP_DIS.val | (1 << (input.index*2))
    conf.regMap.IN_CLK_VAL_EN.val = 1
    conf.regMap.IN_CLK_VAL_TIME.val = 1

    #print(conf.regMap)
    return conf
