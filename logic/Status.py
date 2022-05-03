#
#   Si5394 status holding class
#   Holds the input synchronisation information (LOL/HOLD/LOCK...)
class Status:
    los = [True, True, True, True]  # loss of signal
    oof = [True, True, True, True]  # out of frequency
    lol = True  # loss of lock
    hold = True # hold
    input = -1  # current locked input channel

    #   Create status object from register values
    #   Argument: list of register d,e,f,10,11,12,13
    def __init__(self, res):
        for i in range(4):
            self.los[i] = (res[0] & (0x1 << i)) > 0
            self.oof[i] = (res[0] & (0x10 << i)) > 0
        self.hold = (res[1] & 0x20) > 0
        self.lol = (res[1] & 0x2) > 0

    # String representation
    def __str__(self):
        text = "status:\nlol: " + str(int(self.lol))
        text = text + "\nlos: "
        for i in range(4):
            text = text + str(int(self.los[i]))
        text = text + "\noof: "
        for i in range(4):
            text = text + str(int(self.oof[i]))
        text = text + "\nhold: " + str(int(self.hold))
        text = text + "\ninput: " + str(self.input)
        return text
