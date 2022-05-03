
#
#   This class holds several constants used in this program
#
#

class Constants:
    # configuration file
    CONFIG_FILE = "../last.tgconfig"


    #
    #   UI options
    #

    # Input names
    IN_NAMES = [
        "Input 0\nSide J1",
        "Input 2\nBottom J5/6",
    ]

    # frequency unit strings
    MHZ = "MHz"
    KHZ = "KHz"
    HZ = "Hz"

    # voltage options
    VOLT_OPTIONS = ["1.8 V", "2.5 V", "3.3 V"]

    # termination options
    TERM_OPTIONS = [
        ["31 \u03A9"], # , "46 \u03A9"           # 1.8V
        ["24 \u03A9", "35 \u03A9", "43 \u03A9"], # 2.5V
        ["22 \u03A9", "30 \u03A9", "38 \u03A9"]  # 3.3V
    ]

    #
    #   Max / Min frequency constants
    #

    # maximum / minimum frequencies
    INPUT_F_MIN = 8_000.0
    INPUT_F_MAX_DIFF = 750_000_000.0
    INPUT_F_MAX_CMOS = 250_000_000.0
    # TODO maximum combinations
    OUTPUT_F_MIN = 100.0
    OUTPUT_F_MAX_DIFF = 720_000_000.0
    OUTPUT_F_MAX_CMOS = 250_000_000.0

    # 54 MHz external XTAL
    EXTERNAL_REF_FREQ = 54_000_000

    # maximum internal frequency 14 GHz (f_vco)
    MAX_PLL_F = 14_000_000_000

    # divider max values
    NN_MAX_PWR = 44
    ND_MAX_PWR = 32
    MN_MAX_PWR = 56
    MD_MAX_PWR = 32
    PN_MAX_PWR = 48
    PD_MAX_PWR = 32
    R_MAX_PWR = 25
    NN_MAX_VAL_PWR = 12 # maximum divider value, higher values cause problems --> use R divider additionally

    #
    #   Divider constants
    #

    # allowed error when setting the output frequency with given fvco
    FVCO_TO_MULTI_ERROR = 0.000001

    # allowed error when searching for the gcd of the input frequencies
    # to find a common Fpfd in the given bounds
    GCD_INPUT_ERROR = 0.001

    F_PFD_MAX = 2_000_000   # maximum phase detector frequency
    F_PFD_MIN = 20_000      # minimum phase detector frequency
