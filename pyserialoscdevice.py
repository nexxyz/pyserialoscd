import logging
import pyserialoscutils
import pyserialoscsender
import pyserialoscserialadapter

# legacy /sys/cable values, as accepted by serialosc
CABLE_ROTATIONS = {"l": 0, "0": 0, "t": 90, "9": 90,
                   "r": 180, "1": 180, "b": 270, "2": 270}

INFO_PROPERTIES = ("id", "size", "host", "port", "prefix", "rotation")

# -----------
# Each device will be represented by one endpoint
# -----------


class SerialOscDeviceEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self, serialport, config=None):
    super().__init__("unknown")
    self.config = config
    self.messageprefix = pyserialoscutils.DEFAULT_PREFIX
    self.dispatcher.map("/sys/host", self.set_destination_host)
    self.dispatcher.map("/sys/port", self.set_destination_port)
    self.dispatcher.map("/sys/prefix", self.set_message_prefix)
    self.dispatcher.map("/sys/rotation", self.set_rotation)
    self.dispatcher.map("/sys/cable", self.set_cable)
    self.dispatcher.map("/info", self.get_info)
    self.dispatcher.map("/sys/info", self.get_info)
    for infoproperty in INFO_PROPERTIES:
      self.dispatcher.map("/sys/info/" + infoproperty, self.get_info_property)
    self.serialport = serialport
    self.__messagesender = pyserialoscsender.SerialOscDeviceMessageSender(
      self.messageprefix, pyserialoscutils.DEFAULT_APP_HOST, pyserialoscutils.DEFAULT_APP_PORT)
    self.__serialadapter = pyserialoscserialadapter.SerialAdapter(
      serialport, self.handle_grid_key)
    self.id = "unknown"
    self.friendlyname = serialport
    self.type = "unknown"
    self.size = [0, 0]
    self.rotation = 0
    self.__grid = pyserialoscutils.GridRotation(0, 0)

  def is_alive(self):
    return self.__serialadapter.is_alive()

  # opens the serial port and reads id and size from the device
  def connect(self):
    if (not self.__serialadapter.start()):
      return False
    devicemetadata = self.__serialadapter.get_device_metadata()
    if (devicemetadata is None):
      logging.warning("No monome grid answered on %s", self.serialport)
      self.__serialadapter.stop()
      return False
    self.id = devicemetadata[0]
    self.friendlyname = self.id
    self.size = [devicemetadata[2][0], devicemetadata[2][1]]
    self.type = "monome {}".format(self.size[0] * self.size[1])
    self.__grid = pyserialoscutils.GridRotation(self.size[0], self.size[1])
    return True

  # starts the osc server, using the settings stored for this device id
  def start(self, ip):
    settings = self.config.load(self.id) if self.config else {}
    self.messageprefix = normalize_prefix(
      settings.get("prefix", pyserialoscutils.DEFAULT_PREFIX))
    self.__messagesender.messageprefix = self.messageprefix
    self.__messagesender.destinationhost = settings.get(
      "host", pyserialoscutils.DEFAULT_APP_HOST)
    self.__messagesender.destinationport = settings.get(
      "port", pyserialoscutils.DEFAULT_APP_PORT)
    rotation = settings.get("rotation", 0)
    if (rotation in pyserialoscutils.GridRotation.VALID_DEGREES):
      self.rotation = rotation
      self.__grid.degrees = rotation

    self.friendlyname = self.id
    serverport = settings.get("serverport", 0)
    if (not (serverport and super().start(ip, serverport))):
      if (serverport):
        logging.warning("Stored port %s for device %s is in use, picking another one",
                        serverport, self.id)
      if (not super().start(ip, pyserialoscutils.find_free_port())):
        self.__serialadapter.stop()
        return False
    self.save_config()

    self.__serialadapter.set_grid_led_all(0)
    self.__serialadapter.start_listening()
    self.send_to_app("/sys/connect")
    return True

  def stop(self):
    if (self.running):
      self.send_to_app("/sys/disconnect")
      self.save_config()
    self.__serialadapter.stop()
    super().stop()

  def save_config(self):
    if (not self.config):
      return
    self.config.save(self.id, {
      "serverport": self.port,
      "host": self.__messagesender.destinationhost,
      "port": self.__messagesender.destinationport,
      "prefix": self.messageprefix,
      "rotation": self.rotation})

  def send_to_app(self, path, *osc_arguments):
    self.__messagesender.send_message_to_destination(path, *osc_arguments)

  # replies to /sys/info and /sys/info/<property>
  def reply_info_property(self, infoproperty, host, port):
    send = self.__messagesender.send_message_to_specific_endpoint
    if (infoproperty == "id"):
      send(host, port, "/sys/id", self.id)
    elif (infoproperty == "size"):
      send(host, port, "/sys/size", *self.__grid.app_size())
    elif (infoproperty == "host"):
      send(host, port, "/sys/host", self.__messagesender.destinationhost)
    elif (infoproperty == "port"):
      send(host, port, "/sys/port", self.__messagesender.destinationport)
    elif (infoproperty == "prefix"):
      send(host, port, "/sys/prefix", self.messageprefix)
    elif (infoproperty == "rotation"):
      # like serialosc, also report the size, as it changes with rotation
      if (self.size[0] != self.size[1]):
        self.reply_info_property("size", host, port)
      send(host, port, "/sys/rotation", self.rotation)

  def info_destination(self, arguments):
    # serialosc accepts [host] port, or nothing for the application destination
    host = self.__messagesender.destinationhost
    port = self.__messagesender.destinationport
    if (len(arguments) >= 2):
      host = str(arguments[0])
    if (len(arguments) >= 1):
      port = int(arguments[-1])
    return (host, port)

  # receiving messages for the endpoint
  def set_destination_port(self, requestpath, newport):
    logging.debug(
      "new destination port for device %s requested - %s", self.id, newport)
    oldhost = self.__messagesender.destinationhost
    oldport = self.__messagesender.destinationport
    self.__messagesender.destinationport = int(newport)
    # serialosc tells both the old and the new destination
    self.reply_info_property("port", oldhost, oldport)
    self.reply_info_property("port", oldhost, int(newport))
    self.save_config()

  def set_destination_host(self, requestpath, newhost):
    logging.debug("new host for device %s requested - %s",
            self.id, newhost)
    oldhost = self.__messagesender.destinationhost
    oldport = self.__messagesender.destinationport
    self.__messagesender.destinationhost = str(newhost)
    self.reply_info_property("host", oldhost, oldport)
    self.reply_info_property("host", str(newhost), oldport)
    self.save_config()

  def set_message_prefix(self, requestpath, newmessageprefix):
    logging.debug("new message prefix for device %s requested - %s",
            self.id, newmessageprefix)
    self.messageprefix = normalize_prefix(newmessageprefix)
    self.__messagesender.messageprefix = self.messageprefix
    self.reply_info_property("prefix", *self.info_destination(()))
    self.save_config()

  def set_rotation(self, requestpath, newrotation):
    logging.debug("new rotation for device %s requested - %s",
            self.id, newrotation)
    newrotation = int(newrotation)
    if (newrotation not in pyserialoscutils.GridRotation.VALID_DEGREES):
      logging.error(
        "Only rotations of 0, 90, 180 or 270 are allowed. Got %s. Ignoring it.", newrotation)
      return
    if (newrotation == self.rotation):
      return
    self.rotation = newrotation
    self.__grid.degrees = newrotation
    self.reply_info_property("rotation", *self.info_destination(()))
    self.save_config()

  def set_cable(self, requestpath, cable):
    rotation = CABLE_ROTATIONS.get(str(cable)[:1].lower())
    if (rotation is not None):
      self.set_rotation(requestpath, rotation)

  def get_info(self, requestpath, *arguments):
    host, port = self.info_destination(arguments)
    logging.debug("info requested for device %s to targethost %s and targetport %s",
            self.id, host, port)
    for infoproperty in INFO_PROPERTIES:
      if (infoproperty != "size"):  # rotation includes the size
        self.reply_info_property(infoproperty, host, port)

  def get_info_property(self, requestpath, *arguments):
    self.reply_info_property(
      requestpath.split("/")[-1], *self.info_destination(arguments))

  # receiving key presses from the device
  def handle_grid_key(self, x, y, state):
    appx, appy = self.__grid.to_app(x, y)
    self.__messagesender.send_grid_key(appx, appy, state)

  # sending leds to the device - everything is converted to device coordinates here
  def send_led(self, x, y, value, level):
    devicex, devicey = self.__grid.to_device(x, y)
    if (not self.__grid.on_device(devicex, devicey)):
      return
    if (level):
      self.__serialadapter.set_grid_led_level(devicex, devicey, value)
    else:
      self.__serialadapter.set_grid_led(devicex, devicey, value)

  def send_line(self, appleds, level):
    # appleds: 8 ((x, y), value) in one app row or column, which is still
    # a single row or column on the device after rotation
    deviceleds = sorted(
      (self.__grid.to_device(x, y), value) for (x, y), value in appleds)
    if (not all(self.__grid.on_device(*position) for position, value in deviceleds)):
      logging.debug("Ignoring leds outside of the grid: %s", appleds)
      return
    (startx, starty), _ = deviceleds[0]
    values = [value for position, value in deviceleds]
    isrow = all(position[1] == starty for position, value in deviceleds)
    if (level and isrow):
      self.__serialadapter.set_grid_led_row_level(startx, starty, values)
    elif (level):
      self.__serialadapter.set_grid_led_column_level(startx, starty, values)
    elif (isrow):
      self.__serialadapter.set_grid_led_row(startx, starty, values_to_bitmap(values))
    else:
      self.__serialadapter.set_grid_led_column(startx, starty, values_to_bitmap(values))

  def send_block(self, offsetx, offsety, appvalues, level):
    # appvalues: 64 values of an 8x8 block, row by row
    offsetx = floor_to_quad(offsetx)
    offsety = floor_to_quad(offsety)
    devicevalues = {}
    for index, value in enumerate(appvalues[0:64]):
      position = self.__grid.to_device(offsetx + index % 8, offsety + index // 8)
      if (not self.__grid.on_device(*position)):
        logging.debug("Ignoring block outside of the grid at %s, %s", offsetx, offsety)
        return
      devicevalues[position] = value
    startx = min(x for x, y in devicevalues)
    starty = min(y for x, y in devicevalues)
    rows = [[devicevalues.get((startx + x, starty + y), 0) for x in range(8)]
            for y in range(8)]
    if (level):
      self.__serialadapter.set_grid_led_map_level(
        startx, starty, [value for row in rows for value in row])
    else:
      self.__serialadapter.set_grid_led_map(
        startx, starty, [values_to_bitmap(row) for row in rows])

  def send_row(self, offsetx, y, values, level):
    offsetx = floor_to_quad(offsetx)
    for start in range(0, len(values), 8):
      chunk = values[start:start + 8]
      chunk = chunk + [0] * (8 - len(chunk))
      self.send_line([((offsetx + start + i, y), value)
                      for i, value in enumerate(chunk)], level)

  def send_column(self, x, offsety, values, level):
    offsety = floor_to_quad(offsety)
    for start in range(0, len(values), 8):
      chunk = values[start:start + 8]
      chunk = chunk + [0] * (8 - len(chunk))
      self.send_line([((x, offsety + start + i), value)
                      for i, value in enumerate(chunk)], level)

  # receiving messages for the device
  def default_osc_handler(self, source, *osc_arguments):
    messagepath = osc_arguments[0]
    try:
      # like serialosc, accept floats (e.g. from Pd or TouchOSC) as integers
      parameters = [int(parameter) for parameter in osc_arguments[1:]]
    except (TypeError, ValueError):
      logging.warning("Ignoring %s with non-numeric parameters: %s",
                      messagepath, osc_arguments[1:])
      return
    if (not messagepath.startswith(self.messageprefix + "/")):
      logging.debug("Message path %s does not fit set message prefix %s. Ignoring it",
              messagepath, self.messageprefix)
      return
    elif (messagepath.endswith("/led/all")):
      self.__serialadapter.set_grid_led_all(parameters[0])
    elif (messagepath.endswith("/led/set")):
      self.send_led(parameters[0], parameters[1], parameters[2], False)
    elif (messagepath.endswith("/led/map")):
      self.send_block(parameters[0], parameters[1],
                      bitmaps_to_values(parameters[2:10]), False)
    elif (messagepath.endswith("/led/row")):
      self.send_row(parameters[0], parameters[1],
                    bitmaps_to_values(parameters[2:]), False)
    elif (messagepath.endswith("/led/col")):
      self.send_column(parameters[0], parameters[1],
                       bitmaps_to_values(parameters[2:]), False)
    elif (messagepath.endswith("/led/intensity")):
      self.__serialadapter.set_grid_intensity(parameters[0])
    elif (messagepath.endswith("/led/level/set")):
      self.send_led(parameters[0], parameters[1], parameters[2], True)
    elif (messagepath.endswith("/led/level/all")):
      self.__serialadapter.set_grid_led_all_level(parameters[0])
    elif (messagepath.endswith("/led/level/map")):
      self.send_block(parameters[0], parameters[1], list(parameters[2:]), True)
    elif (messagepath.endswith("/led/level/row")):
      self.send_row(parameters[0], parameters[1], list(parameters[2:]), True)
    elif (messagepath.endswith("/led/level/col")):
      self.send_column(parameters[0], parameters[1], list(parameters[2:]), True)
    else:
      logging.warning(
        "Got unknown OSC device request %s with parameters: %s", messagepath, parameters)


def normalize_prefix(prefix):
  prefix = str(prefix)
  return prefix if prefix.startswith("/") else "/" + prefix


def floor_to_quad(offset):
  return (offset // 8) * 8


def bitmaps_to_values(bitmaps):
  # each bitmap byte holds 8 on/off states, lowest bit first
  return [(bitmap >> bit) & 1 for bitmap in bitmaps for bit in range(8)]


def values_to_bitmap(values):
  bitmap = 0
  for bit, value in enumerate(values[0:8]):
    if (value):
      bitmap |= 1 << bit
  return bitmap
