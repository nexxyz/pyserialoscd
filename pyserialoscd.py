import signal
import logging
import argparse
import time

from pythonosc import dispatcher
import pyserialoscutils
import pyserialoscdevice

# -----------
# The main serialoscd listener
# -----------
class SerialOscMainEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self, onlytheseserialports = [], nottheseserialports = []):
    super().__init__("serialoscmain")
    # Binding handling of incoming requests
    self.dispatcher.map("/serialosc/list", self.list_devices)
    self.dispatcher.map("/serialosc/notify", self.notify_next_change)
    self.devices = []
    self.notifytargets = []
    self.onlytheseserialports = onlytheseserialports
    self.nottheseserialports = nottheseserialports

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

  def get_device_serialportlist(self):
    resultlist = []
    for device in self.devices:
      resultlist.append(device.serialport)

    return resultlist

  def remove_dead_devices(self):
    for device in self.devices:
      if (device.serialport not in pyserialoscutils.list_ports()):
        logging.warning("Device no longer listed as serial port: {}. Removing it".format(device.serialport))
        self.unregisterdevice(device)
        device.stop()
      elif (not device.is_alive()):
        logging.warning("Detected dead device: {}. Removing it.".format(device.friendlyname))
        self.unregisterdevice(device)

  def detect_new_devices(self):
    currentports = pyserialoscutils.list_ports()

    if (self.onlytheseserialports):
      currentports = list(set(currentports).intersection(self.onlytheseserialports))
    elif (self.nottheseserialports):
      currentports = list(set(currentports).difference(self.nottheseserialports))

    for serialport in currentports:
      if (serialport not in self.get_device_serialportlist()):
        # Device
        device = pyserialoscdevice.SerialOscDeviceEndpoint(serialport)
        logging.warning("Detected new device: {}. Adding it.".format(serialport))
        if (device.start("localhost", pyserialoscutils.find_free_port())):
          serialosc.registerdevice(device)
        else:
          logging.error("Could not open device at {}, skipping".format(serialport))    

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
  parser.add_argument("--onlytheseserialports", nargs="*",
      help="If set, all other serial ports than the ones listed here will be ignored. Also disables blacklisting using nottheseserialports")
  parser.add_argument("--nottheseserialports", nargs="*", 
      help="Serial ports that should be ignored - only works if 'onlytheseserialports' is not set")
  parser.add_argument("--serialoscip",
      default="localhost", help="The ip to listen on")
  parser.add_argument("--serialoscport", default=12002, type=int,
      help="The UDP port that main serialosc server will use.")
  parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
      default="INFO", help="The output log level, e.g. ERROR, WARNING, INFO, DEBUG")
  args = parser.parse_args()

  logging.getLogger().setLevel(args.loglevel)

  # Main server
  serialoschost = args.serialoscip
  serialoscport = args.serialoscport
  serialosc = SerialOscMainEndpoint(args.onlytheseserialports, args.nottheseserialports)
  serialosc.detect_new_devices()
  serialosc.start(serialoschost, serialoscport)

  print("pyserialoscd is now listening at {}:{}".format(serialoschost, serialoscport))
  print("Press CTRL-C to stop (if that does not work for some reason please kill python)")
  while True:
    serialosc.remove_dead_devices()
    serialosc.detect_new_devices()
    time.sleep(1)