# taktgenerator
A Python GUI for the Raspberry Pi controlling the FMC Clock Generator.\
For the connection between Raspberry Pi and FMC Clock Generator a adapter is needed.
All 4 output channels of the Si5394 are configurable up to 720 MHz.
The *taktgenerator* can synchronize the output phase to one of two reference input clocks.

![GUI screenshot](/img/ui.png)

# How to use
This implementation is build for the Raspberry Pi Zero W 2 connected to the [FMC Clock Generator](http://www.iamelectronic.com/shop/produkt/fpga-mezzanine-card-fmc-clock-generator/). To interact with the GUI a 1024x600 touch display is used. You can start the software on other systems without the clock generator functionality.
When used as clock generator may disable screen-blanking in the `raspi-config`.

Start class: TaktUI.py\
`python3 TaktUI.py`

# Installation requirements
Following Python libraries are needed:
- PyQt5
- Numpy
- RPi.GPIO (Raspberry)
- smbus (Raspberry)

The software uses the pigs service from pigpio to change the GPIO mode.\
`sudo systemctl enable pigpiod`
