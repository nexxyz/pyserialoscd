from __future__ import absolute_import
import logging
from threading import Thread
from contextlib import closing
import socket
import sys
import os
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc.udp_client import SimpleUDPClient
import json
import re

# chose an implementation, depending on os
#~ if sys.platform == 'cli':
#~ else:
if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
else:
    raise ImportError(
        "Sorry: no implementation for your platform ('%s') available", os.name)


# serialosc defaults for new devices
DEFAULT_PREFIX = "/monome"
DEFAULT_APP_HOST = "127.0.0.1"
DEFAULT_APP_PORT = 8000

# -----------
# To make it a bit easier to send osc messages
# -----------
class OscClientWrapper:
  def __init__(self, targethost, targetport):
    super().__init__()
    self.targethost = map_localhost_to_ip4(targethost)
    self.targetport = targetport
    self.__client = SimpleUDPClient(
        self.targethost, self.targetport)  # Create client

  def send_message(self, address, *osc_arguments):
    logging.debug("Sending message to %s:%s with path %s and data %s",
                  self.targethost, self.targetport, address, osc_arguments)
    self.__client.send_message(address, osc_arguments)

# -----------
# For easy starting and stopping of oscservers
# -----------


class OscServerWrapper:
  def __init__(self, friendlyname):
    super().__init__()
    self.friendlyname = friendlyname
    self.dispatcher = dispatcher.Dispatcher()
    self.dispatcher.set_default_handler(self.default_osc_handler, self)
    self.running = False

  def default_osc_handler(self, source, *osc_arguments):
    logging.warning("WARNING: Unhandled OSC message received by %s. Source: %s, Content %s",
                 self.friendlyname, source, osc_arguments)

  def start(self, host, port):
    self.host = map_localhost_to_ip4(host)
    self.port = port

    try:
      self.__server = osc_server.BlockingOSCUDPServer(
          (self.host, self.port), self.dispatcher)
    except OSError as e:
      logging.warning("WARNING: Error starting OSCUDPServer %s: %s.",
                   self.friendlyname, e)
      return False

    logging.info("Starting OSC server %s on: %s:%s",
                 self.friendlyname, host, port)
    self.__server_thread = Thread(target=self.__server.serve_forever)
    self.__server_thread.start()
    self.running = True
    return True

  def stop(self):
    logging.info("Stopping OSC server: %s", self.friendlyname)
    if (self.running):
      self.__server.shutdown()
      self.__server.server_close()
      self.__server_thread.join()
      self.running = False


def map_localhost_to_ip4(host):
    if (host == "localhost"):
        return "127.0.0.1"
    else:
        return host


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def list_serial_ports():
    portlist = []
    for port in sorted(comports(include_links=True)):
        portlist.append(port.device)

    return portlist

# -----------
# Translates between application and device coordinates for a rotated grid.
# Follows libmonome's conventions so apps behave as with the original serialosc.
# -----------
class GridRotation:
  VALID_DEGREES = (0, 90, 180, 270)

  def __init__(self, devicecols, devicerows, degrees=0):
    self.devicecols = devicecols
    self.devicerows = devicerows
    self.degrees = degrees

  def app_size(self):
    if (self.degrees in (90, 270)):
      return (self.devicerows, self.devicecols)
    return (self.devicecols, self.devicerows)

  def to_device(self, x, y):
    appcols, approws = self.app_size()
    if (self.degrees == 90):
      return (y, appcols - 1 - x)
    elif (self.degrees == 180):
      return (appcols - 1 - x, approws - 1 - y)
    elif (self.degrees == 270):
      return (approws - 1 - y, x)
    return (x, y)

  def to_app(self, x, y):
    appcols, approws = self.app_size()
    if (self.degrees == 90):
      return (appcols - 1 - y, x)
    elif (self.degrees == 180):
      return (appcols - 1 - x, approws - 1 - y)
    elif (self.degrees == 270):
      return (y, approws - 1 - x)
    return (x, y)

  def on_device(self, x, y):
    return 0 <= x < self.devicecols and 0 <= y < self.devicerows


# -----------
# Remembers settings per device id between runs, like serialosc does
# -----------
class DeviceConfigStore:
  def __init__(self, directory=None):
    if (directory is None):
      if (os.name == 'nt'):
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
      else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
      directory = os.path.join(base, "pyserialoscd")
    self.directory = directory

  def path(self, deviceid):
    return os.path.join(self.directory, re.sub(r"[^\w.-]", "_", deviceid) + ".json")

  def load(self, deviceid):
    try:
      with open(self.path(deviceid), encoding="utf-8") as configfile:
        return json.load(configfile)
    except FileNotFoundError:
      return {}
    except (OSError, ValueError) as e:
      logging.warning("Could not read settings for device %s: %s", deviceid, e)
      return {}

  def save(self, deviceid, settings):
    try:
      os.makedirs(self.directory, exist_ok=True)
      with open(self.path(deviceid), "w", encoding="utf-8") as configfile:
        json.dump(settings, configfile, indent=2)
    except OSError as e:
      logging.warning("Could not save settings for device %s: %s", deviceid, e)
