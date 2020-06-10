# pyserialoscd
A python-based simplified serialosc-like implementation

I started to make this to use my neotrellis-monome by @okeyron (see https://github.com/okyeron/neotrellis-monome). Due to the windows version of serialosc requiring an FTDI device to find it in the Windows registry, e.g. teensy-based devices are not picked up by serialoscd. 

And for fun.

Currently the OSC receiving part is implemented, and I am working on the interaction on the serial side of things right now. Afterwards, I will put the two together, and also have autodetection of devices if possible, using a modified version of the com-port-listing from pyserial.

To test it, you can run pyserialoscd and either press the "list" button in something like monome-home.maxpat, or you can run the pyserialtestharness, which will send a list request every second.

As mentioned, current work is on the serial side of things. In this way, pyserialoscserialadapter works as both the implementation and the test file, so you can run it to get basic info on your device right now (you have to adapt the port name (currently it is hardcoded to COM10 which is my neotrellis-monome).
