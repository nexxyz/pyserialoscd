import serial
import time
import pyserialoscsender
import serial.serialutil
from threading import Thread

class SerialListener:
    def __init__(self, serial, messagesender):
        super().__init__()
        self.__serial = serial
        self.running = False
        self.interval = 0.05
        self.__messagesender = messagesender

    def start(self):
        print("Start listening on port {}".format(self.__serial.port))
        self.running = True
        self.__process_thread = Thread(target = self.messagereadloop)
        self.__process_thread.start()

    def stop(self):
        print("Stop listening on port {}".format(self.__serial.port))
        self.running = False
        self.__process_thread.join()

    def messagereadloop(self):
        while(self.running == True):
            while (self.__serial.in_waiting > 0): 
                firstbyte = self.__serial.read()
                print("Got info from serial: {}".format(firstbyte))
                self.dispatchmessage(firstbyte)
            time.sleep(self.interval)

    def dispatchmessage(self, firstbyte):
        # we're receiving device info
        if (firstbyte == b"\x00"):
            self.send_device_info()
        elif (firstbyte == b"\x01"):
            self.send_device_id()
        elif (firstbyte == b"\x20"):
            self.send_key_up()
        elif (firstbyte == b"\x21"):
            self.send_key_down()
        else:
            print("Unknown serial message received: {}".format(firstbyte))
    
    def send_key_up(self):
        x = self.__serial.read()[0]
        y = self.__serial.read()[0]
        self.__messagesender.send_grid_key(x, y, 0)

    def send_key_down(self):
        x = self.__serial.read()[0]
        y = self.__serial.read()[0]
        self.__messagesender.send_grid_key(x, y, 1)

    def send_device_id(self):
        pass

    def send_device_info(self):
        pass

    def read_device_info(self):
        # second is device type
        typelist = [None, "led-grid", "key-grid", "digital-out", "digital-in", "encoder", "analog-in", "analog-out", "tilt", "led-ring"]
        actualtype = typelist[self.__serial.read()[0]]
        print("Device type is {}".format(actualtype))
        
        # third is the number of devices/quads (e.g. 64 buttons per device/quad)
        devicecount = self.__serial.read()[0]
        print("Device count is {}".format(devicecount))

        # FIXME currently just for horizontal 8 led grids - let's make this work for others, too
        devicesize = [devicecount * 8, 8]
        print("Device size is {}".format(devicesize))

        return(actualtype, devicesize)

    def read_device_id(self):
        readid = self.__serial.read(32)
        cleanedid = string_from_bytes(readid)
        print("Cleaned ID is '{}'".format(cleanedid))
        return cleanedid

class SerialAdapter:
    def __init__(self, serialport, messagesender):
        super().__init__()
        print("Initializing serialport {}".format(serialport))
        self.serialport = serialport
        self.__serial = serial.Serial()
        self.__serial.port = self.serialport
        self.__serial.baudrate = 115200
        self.__listener = SerialListener(self.__serial, messagesender)

    def start(self):
        print("Opening adapter {}".format(self.serialport))
        self.__serial.open()
        
        # FIXME: Exception handling if it's not supported?
        self.get_device_information()
        self.__serial.read()
        device_info = self.__listener.read_device_info()
        
        # FIXME: Exception handling if it's not supported?
        self.get_device_id()
        self.__serial.read()
        device_id = self.__listener.read_device_id()

        self.__listener.start()
        return (device_id, device_info)

    def stop(self):
        print("Closing adapter {}".format(self.serialport))
        self.__listener.stop()
        self.__serial.close()

    # device calls
    def set_rotation(self, newrotationdegrees):
        print("new rotation for device {} requested - {}".format(self.serialport, newrotationdegrees))

    def send_info(self, targethost="", targetport=""):
        print("info for device {} requested for {}:{}".format(self.serialport, targethost, targetport))

    def set_grid_led(self, x, y, newstate):
        print("set grid led for device {} requested for {}:{} to state {}".format(self.serialport, x, y, newstate))
        if (newstate):
            self.__serial.write(b'\x11')
        else:
            self.__serial.write(b'\x10')
        self.__serial.write(int_to_byte(x))
        self.__serial.write(int_to_byte(y))

    def set_grid_led_all(self, newstate):
        print("set all grid leds for device {} requested to state {}".format(self.serialport, newstate))
        if (newstate):
            self.__serial.write(b'\x13')
        else:
            self.__serial.write(b'\x12')

    def set_grid_led_map(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        offsety = osc_arguments[2]
        statebitmap = osc_arguments[3:]
        print("set all grid leds for device {} requested for offset {}, {} to state-bitmap {}".format(self.serialport, offsetx, offsety, statebitmap))

    def set_grid_led_column(self, *osc_arguments):
        requestpath = osc_arguments[0]
        x = osc_arguments[1]
        offsety = osc_arguments[2]
        states = osc_arguments[3:]
        print("set column grid leds for device {} requested for x {}, offsety {} to states {}".format(self.serialport, x, offsety, states))

    def set_grid_led_row(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        y = osc_arguments[2]
        states = osc_arguments[3:]
        print("set row grid leds for device {} requested for offsetx {}, y {} to states {}".format(self.serialport, offsetx, y, states))

    def set_grid_intensity(self, newintensity):
        print("set intensity for device {} requested to {}".format(self.id, newintensity))

    def set_grid_led_level(self, x, y, newlevel):
        print("set grid led level for device {} requested for {}:{} to state {}".format(self.serialport, x, y, newlevel))

    def set_grid_led_all_level(self, newlevel):
        print("set all grid led levels for device {} requested to state {}".format(self.serialport, newlevel))

    def set_grid_led_map_level(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        offsety = osc_arguments[2]
        levelbitmap = osc_arguments[3:]
        print("set all grid led levels for device {} requested for offset {}, {} to state-bitmap {}".format(self.serialport, offsetx, offsety, levelbitmap))

    def set_grid_led_column_level(self, *osc_arguments):
        requestpath = osc_arguments[0]
        x = osc_arguments[1]
        offsety = osc_arguments[2]
        levels = osc_arguments[3:]
        print("set columin grid led levels for device {} requested for x {}, offsety {} to state-bitmap {}".format(self.serialport, x, offsety, levels))

    def set_grid_led_row_level(self, *osc_arguments):
        requestpath = osc_arguments[0]
        offsetx = osc_arguments[1]
        y = osc_arguments[2]
        levels = osc_arguments[3:]
        print("set row grid led levels for device {} requested for offsetx {}, y {} to levels {}".format(self.serialport, offsetx, y, levels))

    def set_grid_tilt_sensor(self, sensor, newactivestate):
        print("set tilt sensor activestate for device {} requested for sensor {} to {}".format(self.serialport, sensor, newactivestate))

    def set_ring_led(self, encoder, led, newlevel):
        print("set ring led requested for device {} for encoder {}, led {} to level {}".format(self.serialport, encoder, led, newlevel))

    def set_ring_led_all(self, encoder, newlevel):
        print("set all ring leds requested for device {} for encoder {} to level {}".format(self.serialport, encoder, newlevel))

    def set_ring_led_map(self, *osc_arguments):
        encoder = osc_arguments[0]
        newlevels = osc_arguments[1:]
        print("set ring leds requested for device {} for encoder {} to levels {}".format(self.serialport, encoder, newlevels))

    def set_ring_led_range(self, encoder, ledfrom, ledto, newlevel):
        print("set all ring leds requested for device {} for encoder {}, leds {} to {}, to level {}".format(self.serialport, encoder, ledfrom, ledto, newlevel))

    def get_device_information(self):
        print("Requesting info for adapter {}".format(self.serialport))
        self.__serial.write(b"\x00")

    def get_device_id(self):
        print("Requesting id for adapter {}".format(self.serialport))
        self.__serial.write(b"\x01")

def int_to_byte(integernumber):
    return bytes([integernumber])

def string_from_bytes(bytes):
    encoding = "1252"
    return bytes.decode(encoding).strip(b'\x00'.decode(encoding))