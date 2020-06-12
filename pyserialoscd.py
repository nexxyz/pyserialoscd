import signal
import logging
import argparse

from pythonosc import dispatcher
import pyserialoscutils
import pyserialoscdevice

# -----------
# The main serialoscd listener
# -----------
class SerialOscMainEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self):
    super().__init__("serialoscmain")
    # Binding handling of incoming requests
    self.dispatcher.map("/serialosc/list", self.list_devices)
    self.dispatcher.map("/serialosc/notify", self.notify_next_change)
    self.devices = []
    self.notifytargets = []

  def list_devices(self, requestpath, targethost, targetport):
    logging.debug("list requested via {} for {}:{}".format(requestpath, targethost, targetport))

    for device in self.devices:
      pyserialoscutils.OscClientWrapper(targethost, targetport).send_message("/serialosc/device", device.id, device.type, device.port)

  def notify_next_change(self, requestpath, targethost, targetport):
    logging.debug("notification for next device requested via {} for {}:{}".format(requestpath, targethost, targetport))
    self.notifytargets.append((targethost, targetport))

  def registerdevice(self, device):
    logging.debug("Registering device {}".format(device.id))
    self.devices.append(device)
    for notifytarget in self.notifytargets:
      pyserialoscutils.OscClientWrapper(notifytarget[0], notifytarget[1]).send_message("/serialosc/add", device.id)
    self.notifytargets = []
  
  def unregisterdevice(self, device):
    logging.debug("Unregistering device {}".format(device.id))
    self.devices.remove(device)
    for notifytarget in self.notifytargets:
      pyserialoscutils.OscClientWrapper(notifytarget[0], notifytarget[1]).send_message("/serialosc/remove", device.id)
    self.notifytargets = []

  def stop(self):
    for device in self.devices:
      self.unregisterdevice(device)
      device.stop()
    super().stop()
      

# -----------
# Cleanup
# -----------
def keyboardInterruptHandler(signal, frame):
    logging.debug("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    logging.debug("Stopping serialosc")
    serialosc.stop()
    exit(0)

# -----------
# Main entry point
# -----------
if __name__ == "__main__":
  signal.signal(signal.SIGINT, keyboardInterruptHandler)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.description = "A simplified python implementation of serialoscd for running monomoe grids and homebrew/diy variants"
  parser.add_argument("--serial", required=True, nargs = '+',
      help="The serial ports where your device is connected, e.g. COM* on Windows or /dev/ttyUSB* on other systems")
  parser.add_argument("--serialoscport", default=12002, type=int,
      help="The UDP port that main serialosc server will use.")
  parser.add_argument("--startport", default=15234, type=int,
      help="The UDP port that the first device will open. Further devices will open the port above it (e.g. 15235)")
  parser.add_argument("--ip",
      default="localhost", help="The ip to listen on")
  parser.add_argument("--port",
      type=int, default=5005, help="The port to listen on")
  parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
      default="WARN", help="The output log level, e.g. ERROR, WARNING, INFO, DEBUG")
  args = parser.parse_args()

  logging.getLogger().setLevel(args.loglevel)

  # Main server
  serialoschost = "localhost"
  serialoscport = args.serialoscport
  serialosc = SerialOscMainEndpoint()
  serialosc.start(serialoschost, serialoscport)

  # Device
  startport = args.startport
  for serialport in args.serial:
    device = pyserialoscdevice.SerialOscDeviceEndpoint(serialport)
    if (device.start("localhost", startport)):
      serialosc.registerdevice(device)
      startport += 1
    else:
      logging.error("Could not open device at {}, skipping".format(serialport))

  print("pyserialoscd is now listening at {}:{}".format(serialoschost, serialoscport))
  print("Press CTRL-C to stop (if that does not work for some reason please kill python)")
  while True:
    pass