import platform
from logic.Config import *
from logic.DividerCalc import *
from logic.RegisterMap import *
from logic.SetRegister import *
from logic.Constants import *
from logic.Status import *

if ("arm" in platform.machine()):
    from logic.GPIOControl import *
    from logic.SpiConnection import *
