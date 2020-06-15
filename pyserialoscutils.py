from __future__ import absolute_import
import logging
import socket
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc.udp_client import SimpleUDPClient
from threading import Thread
from contextlib import closing
import pyserialoscutils
import sys
import os

# chose an implementation, depending on os
#~ if sys.platform == 'cli':
#~ else:
if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))


# -----------
# To make it a bit easier to send osc messages
# -----------
class OscClientWrapper:
  def __init__(self, targethost, targetport):
    super().__init__()
    self.targethost = map_localhost_to_ip4(targethost)
    self.targetport = targetport
    self.__client = SimpleUDPClient(self.targethost, self.targetport)  # Create client
  
  def send_message(self, address, *osc_arguments):
    logging.debug("Sending message to {}:{} with path {} and data {}".format(self.targethost, self.targetport, address, osc_arguments))
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
    logging.warn("WARNING: Unhandled OSC message received by {}. Source: {}, Content {}".format(self.friendlyname, source, osc_arguments))

  def start(self, host, port):
    self.host = map_localhost_to_ip4(host)
    self.port = port

    try:
      self.__server = osc_server.BlockingOSCUDPServer((self.host, self.port), self.dispatcher)
    except OSError as e:
      return False

    logging.info("Starting OSC server {} on: {}:{}".format(self.friendlyname, host, port))
    self.__server_thread = Thread(target = self.__server.serve_forever)
    self.__server_thread.start()
    self.running = True
    return True  
    
  def stop(self):
    logging.info("Stopping OSC server: {}".format(self.friendlyname))
    if (self.running):
      self.__server.shutdown()
      self.__server_thread.join()

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

# unused so far - might include in pyserialoscdevice later
def rotate_coordinates(x, y, xsize, ysize, degrees):
  if (degrees == 0):
    return (x, y)
  elif(degrees == 90):
    return (y, xsize - x - 1)
  elif(degrees == 180):
    return (xsize - x - 1, ysize - y - 1)
  elif(degrees == 270):
    return (ysize - y - 1, x)
  else:
    logging.error("Only rotations in increments of 90 are allowed (i.e. 0, 90, 180, 270). Got {}. Ignoring rotation.".format(degrees))
    return (x, y)

def rotate_map(map, degrees):
  returnmap = map
  if (not degrees % 90 == 0):
    logging.error("Only rotations in increments of 90 are allowed (i.e. 0, 90, 180, 270). Got {}. Ignoring rotation.".format(degrees))
    return
  
  rotatetimes = int(degrees / 90)
  for _ in range(rotatetimes):
    returnmap = zip(*returnmap[::-1])
  
  return returnmap