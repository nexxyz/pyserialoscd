import logging
import signal
import argparse
import time
import sys

import pyserialoscutils
import pyserialoscdevice

VERSION = "1.1"

# -----------
# The main serialoscd listener
# -----------


class SerialOscMainEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self, onlytheseserialports=[], nottheseserialports=[], config=None):
    super().__init__("serialoscmain")
    # Binding handling of incoming requests
    self.dispatcher.map("/serialosc/list", self.list_devices)
    self.dispatcher.map("/serialosc/notify", self.notify_next_change)
    self.dispatcher.map("/serialosc/status", self.report_status)
    self.dispatcher.map("/serialosc/version", self.report_version)
    self.dispatcher.map("/serialosc/enable", self.enable)
    self.dispatcher.map("/serialosc/disable", self.disable)
    self.devices = []
    self.notifytargets = []
    # ports that did not answer like a monome, only retried once they reappear
    self.ignoredserialports = set()
    self.enabled = True
    self.onlytheseserialports = onlytheseserialports
    self.nottheseserialports = nottheseserialports
    self.config = config

  def list_devices(self, requestpath, targethost, targetport):
    logging.debug("list requested via %s for %s:%s",
                  requestpath, targethost, targetport)

    for device in list(self.devices):
      pyserialoscutils.OscClientWrapper(targethost, targetport).send_message(
          "/serialosc/device", device.id, device.type, device.port)

  def notify_next_change(self, requestpath, targethost, targetport):
    logging.debug("notification for next device requested via %s for %s:%s",
                  requestpath, targethost, targetport)
    self.notifytargets.append((targethost, targetport))

  def report_status(self, requestpath, targethost, targetport):
    pyserialoscutils.OscClientWrapper(targethost, targetport).send_message(
        "/serialosc/status", int(self.enabled))

  def report_version(self, requestpath, targethost, targetport):
    pyserialoscutils.OscClientWrapper(targethost, targetport).send_message(
        "/serialosc/version", VERSION, "pyserialoscd")

  def enable(self, requestpath):
    logging.info("serialosc enabled")
    self.enabled = True

  def disable(self, requestpath):
    logging.info("serialosc disabled, releasing all devices")
    self.enabled = False

  def notify(self, path, device):
    # like serialosc, a notification request is only valid for one change
    notifytargets, self.notifytargets = self.notifytargets, []
    for notifytarget in notifytargets:
      pyserialoscutils.OscClientWrapper(
          notifytarget[0], notifytarget[1]).send_message(path, device.id, device.type, device.port)

  def registerdevice(self, device):
    logging.debug("Registering device %s", device.id)
    self.devices.append(device)
    self.notify("/serialosc/add", device)

  def unregisterdevice(self, device):
    logging.debug("Unregistering device %s", device.id)
    self.devices.remove(device)
    device.stop()
    self.notify("/serialosc/remove", device)

  def stop(self):
    for device in list(self.devices):
      self.unregisterdevice(device)
    super().stop()

  def get_device_serialportlist(self):
    resultlist = []
    for device in self.devices:
      resultlist.append(device.serialport)

    return resultlist

  def remove_dead_devices(self):
    currentports = pyserialoscutils.list_serial_ports()
    self.ignoredserialports.intersection_update(currentports)
    for device in list(self.devices):
      if (not self.enabled):
        self.unregisterdevice(device)
      elif (device.serialport not in currentports):
        logging.warning(
            "Device no longer listed as serial port: %s. Removing it", device.serialport)
        self.unregisterdevice(device)
      elif (not device.is_alive()):
        logging.warning(
            "Detected dead device: %s. Removing it.", device.friendlyname)
        self.unregisterdevice(device)

  def unique_device_id(self, deviceid):
    # several devices with the same id (e.g. the default "neo-monome") would
    # confuse applications and share their stored settings
    usedids = [device.id for device in self.devices]
    uniqueid = deviceid
    number = 2
    while (uniqueid in usedids):
      uniqueid = "{}-{}".format(deviceid, number)
      number += 1
    return uniqueid

  def detect_new_devices(self):
    if (not self.enabled):
      return

    currentports = pyserialoscutils.list_serial_ports()

    if (self.onlytheseserialports):
      currentports = list(
          set(currentports).intersection(self.onlytheseserialports))
    elif (self.nottheseserialports):
      currentports = list(
          set(currentports).difference(self.nottheseserialports))

    for serialport in currentports:
      if (serialport in self.get_device_serialportlist() or serialport in self.ignoredserialports):
        continue

      device = pyserialoscdevice.SerialOscDeviceEndpoint(serialport, self.config)
      logging.info("Detected new device: %s. Adding it. If it has just been plugged in, please wait a few seconds for it to initialize before pressing any buttons.", serialport)
      if (not device.connect()):
        logging.warning("No monome grid found on %s, ignoring it until it is plugged in again", serialport)
        self.ignoredserialports.add(serialport)
        continue

      device.id = self.unique_device_id(device.id)
      if (device.start(self.host)):
        self.registerdevice(device)
        logging.info("Device %s (%s) on %s is listening on port %s",
                     device.id, device.type, serialport, device.port)
      else:
        logging.error("Could not open device endpoint on %s for serialport %s, skipping",
                      self.host, serialport)

# -----------
# Cleanup
# -----------


def keyboardInterruptHandler(signal, frame):
    logging.debug(
        "KeyboardInterrupt (ID: %s) has been caught. Cleaning up...", signal)
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
  parser.add_argument("--serialoschost",
                      default="localhost", help="The ip/hostname for the main serialosc server to listen on")
  parser.add_argument("--serialoscport", default=12002, type=int,
                      help="The UDP port that main serialosc server will use.")
  parser.add_argument("--configdir", default=None,
                      help="Where the settings (port, prefix, rotation, ...) of each device are stored")
  parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      default="INFO", help="The output log level, e.g. ERROR, WARNING, INFO, DEBUG")
  args = parser.parse_args()

  logging.getLogger().setLevel(args.loglevel)

  # Main server
  serialoschost = args.serialoschost
  serialoscport = args.serialoscport

  serialosc = SerialOscMainEndpoint(
      args.onlytheseserialports, args.nottheseserialports,
      pyserialoscutils.DeviceConfigStore(args.configdir))
  if (not serialosc.start(serialoschost, serialoscport)):
    logging.error("Could not start serialosc main server at %s:%s.\nMaybe the original serialoscd is running?\nYou can also specify a specific port using --serialoscport", serialoschost, serialoscport)
    sys.exit(1)

  print("pyserialoscd is now listening at {}:{}".format(
      serialoschost, serialoscport))
  print("Press CTRL-C to stop (if that does not work for some reason please kill python)")
  while True:
    serialosc.detect_new_devices()
    serialosc.remove_dead_devices()
    time.sleep(1)
