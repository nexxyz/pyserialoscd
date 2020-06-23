from pythonosc import dispatcher
import pyserialoscutils
import pyserialoscsender
import pyserialoscserialadapter
import logging

# -----------
# Each device will be represented by one endpoint
# -----------


class SerialOscDeviceEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self, serialport, messageprefix="/monome", destinationhost="localhost", destinationport=12222):
    super().__init__("unknown")
    self.messageprefix = messageprefix
    self.dispatcher.map("/sys/host", self.set_destination_host)
    self.dispatcher.map("/sys/port", self.set_destination_port)
    self.dispatcher.map("/sys/prefix", self.set_message_prefix)
    self.dispatcher.map("/sys/rotation", self.set_rotation)
    self.dispatcher.map("/info", self.get_info)
    self.dispatcher.map("/sys/info", self.get_info)
    self.serialport = serialport
    self.__messagesender = pyserialoscsender.SerialOscDeviceMessageSender(
        self.messageprefix, destinationhost, destinationport)
    self.__serialadapter = pyserialoscserialadapter.SerialAdapter(
        serialport, self.__messagesender)
    self.id = "unknown"
    self.type = "unknown"
    self.size = [0, 0]
    self.rotation = 0

  def is_alive(self):
    return self.__serialadapter.is_alive()

  def start(self, ip, port):
    if (not self.__serialadapter.start()):
      return False
    self.update_device_metadata()
    return super().start(ip, port)

  def stop(self):
    self.__serialadapter.stop()
    super().stop()

  def update_device_metadata(self):
    devicemetadata = self.__serialadapter.get_device_metadata()
    self.id = devicemetadata[0]
    self.friendlyname = self.id
    self.type = devicemetadata[1][0]
    self.size = [devicemetadata[2][0], devicemetadata[2][1]]

  # receiving messages for the endpoint
  def set_destination_port(self, requestpath, newport):
    logging.debug(
        "new destination port for device %s requested - %s", self.id, newport)
    self.__messagesender.destinationport = newport

  def set_destination_host(self, requestpath, newhost):
    logging.debug("new host for device %s requested - %s", self.id, newhost)
    self.__messagesender.destinationhost = newhost

  def set_message_prefix(self, requestpath, newmessageprefix):
    logging.debug("new message prefix for device %s requested - %s",
                  self.id, newmessageprefix)
    self.messageprefix = newmessageprefix
    self.__messagesender.messageprefix = newmessageprefix

  def set_rotation(self, requestpath, newrotation):
    logging.debug("new rotation for device %s requested - %s",
                  self.id, newrotation)
    self.rotation = newrotation

  def get_info(self, requestpath, destinationhost="", destinationport=""):
    logging.debug("info requested for device %s to targethost %s and targetport %s",
                  self.id, destinationhost, destinationport)
    self.__messagesender.send_info(
        self.id, self.size[0], self.size[1], self.rotation, destinationhost, destinationport)

  # receiving messages for the device
  def default_osc_handler(self, source, *osc_arguments):
    messagepath = osc_arguments[0]
    parameters = osc_arguments[1:]
    if (not messagepath.startswith(self.messageprefix + "/")):
      logging.debug("Message path %s does not fit set message prefix %s. Ignoring it",
                    messagepath, self.messageprefix)
      return
    elif (messagepath.endswith("/led/all")):
      newstate = osc_arguments[1]
      self.__serialadapter.set_grid_led_all(newstate)
    elif (messagepath.endswith("/led/set")):
      x = parameters[0]
      y = parameters[1]
      newstate = parameters[2]
      self.__serialadapter.set_grid_led(x, y, newstate)
    elif (messagepath.endswith("/led/map")):
      offsetx = parameters[0]
      offsety = parameters[1]
      bitmaparray = parameters[2:]
      self.__serialadapter.set_grid_led_map(offsetx, offsety, bitmaparray)
    elif (messagepath.endswith("/led/row")):
      offsetx = parameters[0]
      offsety = parameters[1]
      bitmaparray = parameters[2]
      self.__serialadapter.set_grid_led_row(offsetx, offsety, bitmaparray)
    elif (messagepath.endswith("/led/col")):
      offsetx = parameters[0]
      offsety = parameters[1]
      bitmaparray = parameters[2]
      self.__serialadapter.set_grid_led_column(offsetx, offsety, bitmaparray)
    elif (messagepath.endswith("/led/intensity")):
      newlevel = parameters[0]
      self.__serialadapter.set_grid_intensity(newlevel)
    elif (messagepath.endswith("/led/level/set")):
      x = parameters[0]
      y = parameters[1]
      newlevel = parameters[2]
      self.__serialadapter.set_grid_led_level(x, y, newlevel)
    elif (messagepath.endswith("/led/level/all")):
      newlevel = parameters[0]
      self.__serialadapter.set_grid_led_level(x, y, newlevel)
    elif (messagepath.endswith("/led/level/map")):
      offsetx = parameters[0]
      offsety = parameters[1]
      levelarray = parameters[2:]
      self.__serialadapter.set_grid_led_map_level(offsetx, offsety, levelarray)
    elif (messagepath.endswith("/led/level/row")):
      offsetx = parameters[0]
      offsety = parameters[1]
      bitmaparray = parameters[2:]
      self.__serialadapter.set_grid_led_row_level(offsetx, offsety, levelarray)
    elif (messagepath.endswith("/led/level/col")):
      offsetx = parameters[0]
      offsety = parameters[1]
      bitmaparray = parameters[2:]
      self.__serialadapter.set_grid_led_column_level(
          offsetx, offsety, levelarray)
    else:
      logging.warn(
          "Got unknown OSC device request %s with parameters: %s", messagepath, parameters)
