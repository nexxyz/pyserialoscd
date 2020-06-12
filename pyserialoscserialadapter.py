import serial
import logging
import time
import pyserialoscsender
import serial.serialutil
from threading import Thread

# -----------
# This is processing stuff coming from the device
# -----------
class SerialListener:
    def __init__(self, serial, messagesender):
        super().__init__()
        self.__serial = serial
        self.running = False
        self.interval = 0.02
        self.__messagesender = messagesender

    def start(self):
        logging.debug("Start listening on port {}".format(self.__serial.port))
        self.running = True
        self.__process_thread = Thread(target = self.messagereadloop)
        self.__process_thread.start()

    def stop(self):
        logging.debug("Stop listening on port {}".format(self.__serial.port))
        self.running = False
        self.__process_thread.join()

    def messagereadloop(self):
        while(self.running == True):
            while (self.__serial.in_waiting > 0): 
                firstbyte = self.__serial.read()
                self.dispatchmessage(firstbyte)
            time.sleep(self.interval)

    def dispatchmessage(self, firstbyte):
        # we're receiving device info
        if (firstbyte == b"\x00"):
            self.process_device_info()
        elif (firstbyte == b"\x01"):
            self.process_device_id()
        elif (firstbyte == b"\x02"):
            self.process_grid_offset()
        elif (firstbyte == b"\x03"):
            self.process_grid_size()
        elif (firstbyte == b"\x04"):
            self.process_device_addr()
        elif (firstbyte == b"\x0F"):
            self.process_device_firmware_version()
        elif (firstbyte == b"\x20"):
            self.process_key_up()
        elif (firstbyte == b"\x21"):
            self.process_key_down()
        else:
            logging.warn("Unknown serial message received: {}. Ignoring by flushing rest. Might cause instability.".format(firstbyte))
            self.__serial.flush()
    
    def process_key_up(self):
        x = self.__serial.read()[0]
        y = self.__serial.read()[0]
        self.__messagesender.send_grid_key(x, y, 0)

    def process_key_down(self):
        x = self.__serial.read()[0]
        y = self.__serial.read()[0]
        self.__messagesender.send_grid_key(x, y, 1)

    def process_device_id(self):
        self.read_device_id
        # Maybe want to push this back to osc

    def process_device_info(self):
        self.read_device_info
        # Maybe want to push this back to osc

    def process_grid_offset(self):
        gridnumber = self.__serial.read()[0]
        xoffset = self.__serial.read()[0]
        yoffset = self.__serial.read()[0]
        return(gridnumber, xoffset, yoffset)
    
    def process_grid_size(self):
        xsize = self.__serial.read()[0]
        ysize = self.__serial.read()[0]
        return(xsize, ysize)

    def process_device_addr(self):
        gridaddr = self.__serial.read()[0]
        gridtype = self.__serial.read()[0]
        return(gridaddr, gridtype)

    def process_device_firmware_version(self):
        versionbytes = self.__serial.read(0)
        return string_from_bytes(versionbytes)

    def read_device_info(self):
        # second is device type
        typelist = [None, "led-grid", "key-grid", "digital-out", "digital-in", "encoder", "analog-in", "analog-out", "tilt", "led-ring"]
        actualtype = typelist[self.__serial.read()[0]]
        logging.info("Device type is {}".format(actualtype))

        if (actualtype not in typelist[1:2]):
            logging.debug("Warning!!! Device-Type probably not supported: {}. Only grids are supported for now".format(actualtype))
        
        # third is the number of devices/quads (e.g. 64 buttons per device/quad)
        devicecount = self.__serial.read()[0]
        logging.debug("Device count is {}".format(devicecount))

        # FIXME currently just for horizontal 8 led grids - let's make this work for others, too
        logging.debug("Device count is {}".format(devicecount))

        return(actualtype, devicecount)

    def read_device_id(self):
        readid = self.__serial.read(32)
        cleanedid = string_from_bytes(readid)
        logging.debug("Cleaned ID is '{}'".format(cleanedid))
        return cleanedid

    
# -----------
# This is triggering commands on the device
# -----------
class SerialAdapter:
    def __init__(self, serialport, messagesender):
        super().__init__()
        logging.debug("Initializing serial port {}".format(serialport))
        self.serialport = serialport
        self.__serial = serial.Serial()
        self.__serial.port = self.serialport
        self.__serial.baudrate = 115200
        self.__listener = SerialListener(self.__serial, messagesender)

    def start(self):
        logging.info("Opening serial port {}".format(self.serialport))
        
        try:
            self.__serial.open()
            # Flush any remaining fragments
            self.__serial.flush()
            self.__listener.start()
        except serial.serialutil.SerialException as e:
            logging.error("Could not open port {}, Exception was {}".format(self.serialport, e))
            return False
        
        return True

    def stop(self):
        logging.info("Closing serial port {}".format(self.serialport))
        self.__listener.stop()
        if (self.__serial.isOpen()):
            self.__serial.close()

    def get_device_metadata(self):
        # FIXME: Exception handling if it's not supported?
        self.request_device_information()
        self.__serial.read()
        device_info = self.__listener.read_device_info()
        
        # FIXME: Exception handling if it's not supported?
        self.request_device_id()
        self.__serial.read()
        device_id = self.__listener.read_device_id()

        self.request_device_size()
        self.__serial.read()
        grid_size = self.__listener.process_grid_size()

        return (device_id, device_info, grid_size)

    # device calls
    def set_grid_led(self, x, y, newstate):
        logging.debug("set grid led for device {} requested for {}:{} to state {}".format(self.serialport, x, y, newstate))
        message = b""
        if (newstate):
            message += b'\x11'
        else:
            message += b'\x10'
        message += int_to_byte(x)
        message += int_to_byte(y)
        self.__serial.write(message)

    def set_grid_led_all(self, newstate):
        logging.debug("set all grid leds for device {} requested to state {}".format(self.serialport, newstate))
        if (newstate):
            self.__serial.write(b'\x13')
        else:
            self.__serial.write(b'\x12')

    def set_grid_led_map(self, offsetx, offsety, bitmaparray):
        logging.debug("set map grid leds for device {} requested for offset {}, {} to state-bitmap {}".format(self.serialport, offsetx, offsety, bitmaparray))
        message = b""
        message += b'\x14'
        message += int_to_byte(offsetx)
        message += int_to_byte(offsety)
        for bitmap in bitmaparray:
            message += int_to_byte(bitmap)
        self.__serial.write(message)

    def set_grid_led_row(self, offsetx, offsety, bitmaparray):
        logging.debug("set row grid leds for device {} requested for offsetx {}, y {} to states {}".format(self.serialport, offsetx, offsety, bitmaparray))
        message = b""
        message += b'\x15'
        message += int_to_byte(offsetx)
        message += int_to_byte(offsety)
        for bitmap in bitmaparray:
            message += int_to_byte(bitmap)
        self.__serial.write(message)

    def set_grid_led_column(self, offsetx, offsety, bitmaparray):
        logging.debug("set column grid leds for device {} requested for x {}, offsety {} to states {}".format(self.serialport, offsetx, offsety, bitmaparray))
        message = b""
        message += b'\x16'
        message += int_to_byte(offsetx)
        message += int_to_byte(offsety)
        for bitmap in bitmaparray:
            message += int_to_byte(bitmap)
        self.__serial.write(message)

    def set_grid_intensity(self, newintensity):
        logging.debug("set intensity for device {} requested to {}".format(self.serialport, newintensity))
        message = b""
        message += b'\x17'
        message += int_to_byte(newintensity)
        self.__serial.write(message)

    def set_grid_led_level(self, x, y, newlevel):
        logging.debug("set grid led level for device {} requested for {}:{} to state {}".format(self.serialport, x, y, newlevel))
        message = b""
        message += b'\x18'
        message += int_to_byte(x)
        message += int_to_byte(y)
        message += int_to_byte(newlevel)
        self.__serial.write(message)

    def set_grid_led_all_level(self, newlevel):
        logging.debug("set all grid led levels for device {} requested to state {}".format(self.serialport, newlevel))
        message = b""
        message += b'\x19'
        message += int_to_byte(newlevel)
        self.__serial.write(message)

    def set_grid_led_map_level(self, offsetx, offsety, levelarray):
        logging.debug("set all grid led levels for device {} requested for offset {}, {} to state-bitmap {}".format(self.serialport, offsetx, offsety, levelarray))
        message = b""
        message += b'\x1A'
        message += int_to_byte(offsetx)
        message += int_to_byte(offsety)
        for level in levelarray:
            message += int_to_byte(level)
        self.__serial.write(message)

    def set_grid_led_row_level(self, offsetx, offsety, levelarray):
        logging.debug("set row grid led levels for device {} requested for offsetx {}, y {} to levels {}".format(self.serialport, offsetx, offsety, levelarray))
        message = b""
        message += b'\x1B'
        message += int_to_byte(offsetx)
        message += int_to_byte(offsety)
        for level in levelarray:
            message += int_to_byte(level)
        self.__serial.write(message)

    def set_grid_led_column_level(self, offsetx, offsety, levelarray):
        logging.debug("set column grid led levels for device {} requested for x {}, offsety {} to state-bitmap {}".format(self.serialport, offsetx, offsety, levelarray))
        message = b""
        message += b'\x1C'
        message += int_to_byte(offsetx)
        message += int_to_byte(offsety)
        for level in levelarray:
            message += int_to_byte(level)
        self.__serial.write(message)

    def request_device_information(self):
        logging.debug("Requesting info for adapter {}".format(self.serialport))
        self.__serial.write(b"\x00")

    def request_device_id(self):
        logging.debug("Requesting id for adapter {}".format(self.serialport))
        self.__serial.write(b"\x01")

    def request_device_size(self):
        logging.debug("Requesting size for adapter {}".format(self.serialport))
        self.__serial.write(b"\x05")

def int_to_byte(integernumber):
    return bytes([integernumber])

def string_from_bytes(bytes):
    encoding = "1252"
    return bytes.decode(encoding).strip(b'\x00'.decode(encoding))