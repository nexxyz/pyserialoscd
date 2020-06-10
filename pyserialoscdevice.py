from pythonosc import dispatcher
import pyserialoscutils

# -----------
# Each device will be represented by one endpoint
# -----------
class serialosc_device(pyserialoscutils.oscserver_wrapper):
  def __init__(self, deviceid, devicetype, messageprefix = "", size=[16, 8], destinationhost = "", destinationport = 0, rotation = 0):
    super().__init__(deviceid)
    
    # set device info
    self.id = deviceid
    self.type = devicetype
    self.messageprefix = messageprefix
    self.size = size
    self.destinationport = destinationport
    self.destinationhost = destinationhost
    self.rotation = rotation

    self.dispatcher = dispatcher.Dispatcher()
    self.dispatcher.map("/sys/port", self.set_destination_port)
    self.dispatcher.map("/sys/host", self.set_destination_host)
    self.dispatcher.map("/sys/prefix", self.set_message_prefix)
    self.dispatcher.map("/sys/rotation", self.set_rotation)
    self.dispatcher.map("/sys/info", self.send_info)

    self.dispatcher.map("/grid/led/set", self.set_grid_led)
    self.dispatcher.map("/grid/led/all", self.set_grid_led_all)
    self.dispatcher.map("/grid/led/map", self.set_grid_led_map)
    self.dispatcher.map("/grid/led/col", self.set_grid_led_column)
    self.dispatcher.map("/grid/led/row", self.set_grid_led_row)
    self.dispatcher.map("/grid/led/intensity", self.set_grid_intensity)
    self.dispatcher.map("/grid/led/level/set", self.set_grid_led_level)
    self.dispatcher.map("/grid/led/level/all", self.set_grid_led_all_level)
    self.dispatcher.map("/grid/led/level/map", self.set_grid_led_map_level)
    self.dispatcher.map("/grid/led/level/col", self.set_grid_led_column_level)
    self.dispatcher.map("/grid/led/level/row", self.set_grid_led_row_level)
    self.dispatcher.map("/grid/tilt", self.set_grid_tilt_sensor)
    self.dispatcher.map("/ring/set", self.set_ring_led)
    self.dispatcher.map("/ring/all", self.set_ring_led_all)
    self.dispatcher.map("/ring/map", self.set_ring_led_map)
    self.dispatcher.map("/ring/range", self.set_ring_led_range)

  # osc communication calls
  def set_destination_port(self, requestpath, newport):
      print("new destination port for device requested via {} - {}".format(requestpath, newport))
      self.destinationport = newport

  def set_destination_host(self, requestpath, newhost):
      print("new host for device requested via {} - {}".format(requestpath, newhost))
      self.destinationhost = newhost

  def set_message_prefix(self, requestpath, newmessageprefix):
      print("new prefix for device requested via {} - {}".format(requestpath, newmessageprefix))
      self.messageprefix = newmessageprefix

  # device calls
  def set_rotation(self, requestpath, newrotationdegrees):
      print("new rotation for device requested via {} - {}".format(requestpath, newrotationdegrees))

  def send_info(self, requestpath, targethost="", targetport=""):
      print("info for device requested via {} for {}:{}".format(requestpath, targethost, targetport))

  def set_grid_led(self, requestpath, x, y, newstate):
      print("set grid led for device requested via {} for {}:{} to state {}".format(requestpath, x, y, newstate))

  def set_grid_led_all(self, requestpath, newstate):
      print("set all grid leds for device requested via {} to state {}".format(requestpath, newstate))

  def set_grid_led_map(self, requestpath, *osc_arguments):
      requestpath = osc_arguments[0]
      offsetx = osc_arguments[1]
      offsety = osc_arguments[2]
      statebitmap = osc_arguments[3:]
      print("set all grid leds for device requested via {} for offset {}, {} to state-bitmap {}".format(requestpath, offsetx, offsety, statebitmap))

  def set_grid_led_column(self, requestpath, *osc_arguments):
      requestpath = osc_arguments[0]
      x = osc_arguments[1]
      offsety = osc_arguments[2]
      states = osc_arguments[3:]
      print("set column grid leds for device requested via {} for x {}, offsety {} to states {}".format(requestpath, x, offsety, states))

  def set_grid_led_row(self, requestpath, *osc_arguments):
      requestpath = osc_arguments[0]
      offsetx = osc_arguments[1]
      y = osc_arguments[2]
      states = osc_arguments[3:]
      print("set row grid leds for device requested via {} for offsetx {}, y {} to states {}".format(requestpath, offsetx, y, states))

  def set_grid_intensity(self, requestpath, newintensity):
      print("set intensity for device requested via {} to {}".format(requestpath, newintensity))

  def set_grid_led_level(self, requestpath, x, y, newlevel):
      print("set grid led level for device requested via {} for {}:{} to state {}".format(requestpath, x, y, newlevel))

  def set_grid_led_all_level(self, requestpath, newlevel):
      print("set all grid led levels for device requested via {} to state {}".format(requestpath, newlevel))

  def set_grid_led_map_level(self, requestpath, *osc_arguments):
      requestpath = osc_arguments[0]
      offsetx = osc_arguments[1]
      offsety = osc_arguments[2]
      levelbitmap = osc_arguments[3:]
      print("set all grid led levels for device requested via {} for offset {}, {} to state-bitmap {}".format(requestpath, offsetx, offsety, levelbitmap))

  def set_grid_led_column_level(self, requestpath, *osc_arguments):
      requestpath = osc_arguments[0]
      x = osc_arguments[1]
      offsety = osc_arguments[2]
      levels = osc_arguments[3:]
      print("set columin grid led levels for device requested via {} for x {}, offsety {} to state-bitmap {}".format(requestpath, x, offsety, levels))

  def set_grid_led_row_level(self, requestpath, *osc_arguments):
      requestpath = osc_arguments[0]
      offsetx = osc_arguments[1]
      y = osc_arguments[2]
      levels = osc_arguments[3:]
      print("set row grid led levels for device requested via {} for offsetx {}, y {} to levels {}".format(requestpath, offsetx, y, levels))

  def set_grid_tilt_sensor(self, requestpath, sensor, newactivestate):
      print("set tilt sensor activestate for device requested via {} for sensor {} to {}".format(requestpath, sensor, newactivestate))

  def set_ring_led(self, requestpath, encoder, led, newlevel):
      print("set ring led requested via {} for encoder {}, led {} to level {}".format(requestpath, encoder, led, newlevel))

  def set_ring_led_all(self, requestpath, encoder, newlevel):
      print("set all ring leds requested via {} for encoder {} to level {}".format(requestpath, encoder, newlevel))

  def set_ring_led_map(self, requestpath, *osc_arguments):
      encoder = osc_arguments[0]
      newlevels = osc_arguments[1:]
      print("set ring leds requested via {} for encoder {} to levels {}".format(requestpath, encoder, newlevels))

  def set_ring_led_range(self, requestpath, encoder, ledfrom, ledto, newlevel):
      print("set all ring leds requested via {} for encoder {}, leds {} to {}, to level {}".format(requestpath, encoder, ledfrom, ledto, newlevel))
