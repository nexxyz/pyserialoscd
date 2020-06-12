import signal

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
    print("list requested via {} for {}:{}".format(requestpath, targethost, targetport))

    for device in self.devices:
      pyserialoscutils.OscClientWrapper(targethost, targetport).send_message("/serialosc/device", device.id, device.type, device.port)

  def notify_next_change(self, requestpath, targethost, targetport):
    print("notification for next device requested via {} for {}:{}".format(requestpath, targethost, targetport))
    self.notifytargets.append((targethost, targetport))

  def registerdevice(self, device):
    print("Registering device {}".format(device.id))
    self.devices.append(device)
    for notifytarget in self.notifytargets:
      pyserialoscutils.OscClientWrapper(notifytarget[0], notifytarget[1]).send_message("/serialosc/add", device.id)
    self.notifytargets = []
  
  def unregisterdevice(self, device):
    print("Unregistering device {}".format(device.id))
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
# Utils
# -----------
def make_tuple_printable(*args):
  return " ".join(map(str, args))

# -----------
# Cleanup
# -----------
def keyboardInterruptHandler(signal, frame):
    print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    print("Stopping serialosc")
    serialosc.stop()
    exit(0)

# -----------
# Main entry point
# -----------
if __name__ == "__main__":
  signal.signal(signal.SIGINT, keyboardInterruptHandler)

  # Main server
  serialosc = SerialOscMainEndpoint()
  serialosc.start("localhost", 12002)

  # Device
  device = pyserialoscdevice.SerialOscDeviceEndpoint("COM3")
  device.start("localhost", 12235)
  serialosc.registerdevice(device)
  
  print("Press CTRL-C to stop")
  while True:
    pass