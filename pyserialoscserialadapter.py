import serial
import serial.tools

class SerialAdapter:
    def __init__(self, serialport):
        print("Initializing serialport {}".format(serialport))
        self.serialport = serialport
        self.__serial = serial.Serial()
        self.__serial.port = self.serialport
        self.__serial.baudrate = 115200

    def open(self):
        print("Opening adapter {}".format(self.serialport))
        self.__serial.open()

    def close(self):
        print("Closing adapter {}".format(self.serialport))
        self.__serial.close()

    def get_device_information(self):
        print("Getting info for adapter {}".format(self.serialport))
        self.__serial.write(b"\x00")

        # first is always 0x00
        self.__serial.read() 

        # second is device type
        typelist = [None, "led-grid", "key-grid", "digital-out", "digital-in", "encoder", "analog-in", "analog-out", "tilt", "led-ring"]
        actualtype = typelist[self.__serial.read()[0]]
        print("Device type is {}".format(actualtype))
        
        # third is the number of quads (64 buttons)
        devicesize = 64*(self.__serial.read()[0])
        print("Device size is {}".format(devicesize))

adapter = SerialAdapter("COM10")
adapter.open()
adapter.get_device_information()
adapter.close()