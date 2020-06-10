import serial
import time
from threading import Thread

class SerialListener:
    def __init__(self, serial):
        super().__init__()
        self.__serial = serial
        self.pollinginterval = 1
        self.__actionqueue = []
        self.running = False
        self.id = ""

    def start(self):
        print("Start listening on port {}".format(self.__serial.port))
        self.__running = True
        self.__process_thread = Thread(target = self.messagereadloop)
        self.__process_thread.start()

    def stop(self):
        print("Stop listening on port {}".format(self.__serial.port))
        self.__running = False
        self.__process_thread.join()

    def messagereadloop(self):
        while(self.__running == True):
            if(not self.__actionqueue):
               print("Nothing to do, should poll monome")
            else:
                action = self.__actionqueue[0]
                self.executeaction(action)
                self.__actionqueue.remove(action)

            time.sleep(self.pollinginterval)

    def executeaction(self, action, *args):
        self.get_device_information()

    def qeueaction(self, action, *args):
        self.__actionqueue.append(action)

    # device calls
    def set_rotation(self, newrotationdegrees):
        print("new rotation for device {} requested - {}".format(self.id, newrotationdegrees))

    def send_info(self, targethost="", targetport=""):
        print("info for device {} requested for {}:{}".format(self.id, targethost, targetport))

    def set_grid_led(self, x, y, newstate):
        print("set grid led for device {} requested for {}:{} to state {}".format(self.id, x, y, newstate))

    def set_grid_led_all(self, newstate):
        print("set all grid leds for device {} requested to state {}".format(self.id, newstate))

    def set_grid_led_map(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        offsety = osc_arguments[2]
        statebitmap = osc_arguments[3:]
        print("set all grid leds for device {} requested for offset {}, {} to state-bitmap {}".format(self.id, offsetx, offsety, statebitmap))

    def set_grid_led_column(self, *osc_arguments):
        requestpath = osc_arguments[0]
        x = osc_arguments[1]
        offsety = osc_arguments[2]
        states = osc_arguments[3:]
        print("set column grid leds for device {} requested for x {}, offsety {} to states {}".format(self.id, x, offsety, states))

    def set_grid_led_row(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        y = osc_arguments[2]
        states = osc_arguments[3:]
        print("set row grid leds for device {} requested for offsetx {}, y {} to states {}".format(self.id, offsetx, y, states))

    def set_grid_intensity(self, newintensity):
        print("set intensity for device {} requested to {}".format(self.id, newintensity))

    def set_grid_led_level(self, x, y, newlevel):
        print("set grid led level for device {} requested for {}:{} to state {}".format(self.id, x, y, newlevel))

    def set_grid_led_all_level(self, newlevel):
        print("set all grid led levels for device {} requested to state {}".format(self.id, newlevel))

    def set_grid_led_map_level(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        offsety = osc_arguments[2]
        levelbitmap = osc_arguments[3:]
        print("set all grid led levels for device {} requested for offset {}, {} to state-bitmap {}".format(self.id, offsetx, offsety, levelbitmap))

    def set_grid_led_column_level(self, *osc_arguments):
        requestpath = osc_arguments[0]
        x = osc_arguments[1]
        offsety = osc_arguments[2]
        levels = osc_arguments[3:]
        print("set columin grid led levels for device {} requested for x {}, offsety {} to state-bitmap {}".format(self.id, x, offsety, levels))

    def set_grid_led_row_level(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        y = osc_arguments[2]
        levels = osc_arguments[3:]
        print("set row grid led levels for device {} requested for offsetx {}, y {} to levels {}".format(self.id, offsetx, y, levels))

    def set_grid_tilt_sensor(self, sensor, newactivestate):
        print("set tilt sensor activestate for device {} requested for sensor {} to {}".format(self.id, sensor, newactivestate))

    def set_ring_led(self, encoder, led, newlevel):
        print("set ring led requested for device {} for encoder {}, led {} to level {}".format(self.id, encoder, led, newlevel))

    def set_ring_led_all(self, encoder, newlevel):
        print("set all ring leds requested for device {} for encoder {} to level {}".format(self.id, encoder, newlevel))

    def set_ring_led_map(self, *osc_arguments):
        encoder = osc_arguments[0]
        newlevels = osc_arguments[1:]
        print("set ring leds requested for device {} for encoder {} to levels {}".format(self.id, encoder, newlevels))

    def set_ring_led_range(self, encoder, ledfrom, ledto, newlevel):
        print("set all ring leds requested for device {} for encoder {}, leds {} to {}, to level {}".format(self.id, encoder, ledfrom, ledto, newlevel))

    def get_device_information(self):
        print("Requesting info for adapter {}".format(self.__serial.port))
        self.__serial.write(b"\x00")
        self.__serial.read()
        # second is device type
        typelist = [None, "led-grid", "key-grid", "digital-out", "digital-in", "encoder", "analog-in", "analog-out", "tilt", "led-ring"]
        actualtype = typelist[self.__serial.read()[0]]
        print("Device type is {}".format(actualtype))
        
        # third is the number of quads (64 buttons per quad)
        devicesize = 64*(self.__serial.read()[0])
        print("Device size is {}".format(devicesize))


class SerialAdapter:
    def __init__(self, serialport):
        super().__init__()
        print("Initializing serialport {}".format(serialport))
        self.serialport = serialport
        self.__serial = serial.Serial()
        self.__serial.port = self.serialport
        self.__serial.baudrate = 115200
        self.__listener = SerialListener(self.__serial)

    def open(self):
        print("Opening adapter {}".format(self.serialport))
        self.__serial.open()
        self.__listener.start()

    def close(self):
        print("Closing adapter {}".format(self.serialport))
        self.__listener.stop()
        self.__serial.close()

    def addaction(self, action):
        self.__listener.qeueaction("bla")

adapter = SerialAdapter("COM10")
adapter.open()
adapter.addaction("deviceinfo")
time.sleep(1)
adapter.close()