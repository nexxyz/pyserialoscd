import signal

from pythonosc import dispatcher
import pyserialoscutils
import pyserialoscdevice

# -----------
# The main serialoscd listener
# -----------
class serialosc_main_endpoint(pyserialoscutils.oscserver_wrapper):
  def __init__(self, device):
    super().__init__("serialoscmain")
    # Binding handling of incoming requests
    self.dispatcher.map("/serialosc/list", self.list_devices)
    self.dispatcher.map("/serialosc/notify", self.notify_next_change)
    self.device = device

  def list_devices(self, requestpath, targethost, targetport):
    print("list requested via {} for {}:{}".format(requestpath, targethost, targetport))
    pyserialoscutils.oscclient_wrapper(targethost, targetport).send_message("/serialosc/device", self.device.id, self.device.type, 12235)

  def notify_next_change(self, requestpath, targethost, targetport):
    print("notification for next device requested via {} for {}:{}".format(requestpath, targethost, targetport))

# -----------
# Each device will be represented by one endpoint
# -----------
class serialosc_device_endpoint(pyserialoscutils.oscserver_wrapper):
  def __init__(self, device):
    super().__init__(device.friendlyname)
    self.device = device
    self.dispatcher = dispatcher.Dispatcher()
    self.dispatcher.map("/info", self.send_info)
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

  def set_port(self, requestpath, newport):
      print("new port for device requested via {} - {}".format(requestpath, newport))

  def set_prefix(self, requestpath, newprefix):
      print("new prefix for device requested via {} - {}".format(requestpath, newprefix))

  def set_host(self, requestpath, newhost):
      print("new host for device requested via {} - {}".format(requestpath, newhost))

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

# -----------
# Utils
# -----------
def make_tuple_printable(*args):
  return " ".join(map(str, args))

# -----------
# Cleanup
# -----------
def keyboardInterruptHandler(signal, frame):
    print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    print("Stopping devices")
    device.stop()
    print("Stopping serialosc")
    serialosc.stop()
    exit(0)

# -----------
# Main entry point
# -----------
if __name__ == "__main__":
  signal.signal(signal.SIGINT, keyboardInterruptHandler)

  # Serial device
  device = pyserialoscdevice.serialdevice() 

  # Main server
  serialosc = serialosc_main_endpoint(device)
  serialosc.start("127.0.0.1", 12002)

  # Device thread handling
  device = serialosc_device_endpoint(device)
  device.start("127.0.0.1", 12235)
  
  print("Press CTRL-C to stop")
  while True:
    pass