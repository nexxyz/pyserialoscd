from pythonosc import dispatcher
import pyserialoscutils
import pyserialoscsender
import pyserialoscserialadapter

# -----------
# Each device will be represented by one endpoint
# -----------
class SerialOscDeviceEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self, comport, messageprefix = "/monome", destinationhost = "localhost", destinationport = 12222):
    super().__init__("unknown")
    self.messageprefix = messageprefix
    self.dispatcher.map("/sys/host", self.set_destination_host)
    self.dispatcher.map("/sys/port", self.set_destination_port)
    self.dispatcher.map("/sys/prefix", self.set_message_prefix)
    self.dispatcher.map("/sys/rotation", self.set_rotation)
    self.dispatcher.map("/info", self.get_info)
    self.dispatcher.map("/sys/info", self.get_info)

    self.__messagesender = pyserialoscsender.SerialOscDeviceMessageSender(self.messageprefix, destinationhost, destinationport)
    self.__serialadapter = pyserialoscserialadapter.SerialAdapter(comport, self.__messagesender)
    self.id = "unknown"
    self.type = "unknown"
    self.size = [0, 0]
    self.rotation = 0
    

  def start(self, ip, port):
    devicemetadata = self.__serialadapter.start()
    self.id = devicemetadata[0]
    self.friendlyname = self.id
    self.type = devicemetadata[1][0]
    self.size = devicemetadata[1][1]
    super().start(ip, port)
  
  def stop(self):
    self.__serialadapter.stop()
    super().stop()

  # receiving messages for the endpoint
  def set_destination_port(self, requestpath, newport):
    print("new destination port for device {} requested - {}".format(self.id, newport))
    self.__messagesender.destinationport = newport

  def set_destination_host(self, requestpath, newhost):
    print("new host for device {} requested - {}".format(self.id, newhost))
    self.__messagesender.destinationhost = newhost

  def set_message_prefix(self, requestpath, newmessageprefix):
    print("new message prefix for device {} requested - {}".format(self.id, newmessageprefix))
    self.messageprefix = newmessageprefix
    self.__messagesender.messageprefix = newmessageprefix
    
  def set_rotation(self, requestpath, newrotation):
    print("new rotation for device {} requested - {}".format(self.id, newrotation))
    self.rotation = newrotation

  def get_info(self, requestpath, destinationhost = "", destinationport = ""):
    print("info requested for device {} to targethost {} and targetport {}".format(self.id, destinationhost, destinationport))
    self.__messagesender.send_info(self.id, self.size[0], self.size[1], self.rotation, destinationhost, destinationport)
  
  # receiving messages for the device
  def default_osc_handler(self, source, *osc_arguments):
    print("Processing device OSC command for device {}, Source: {}, Content {}".format(self.id, source, osc_arguments))

    messagepath = osc_arguments[0]
    if (not messagepath.startswith(self.messageprefix + "/")):
      print("Message path {} does not fit set message prefix {}. Ignoring it".format(messagepath, self.messageprefix))
      return
    elif (messagepath.endswith("/led/all")):
      targetstate = osc_arguments[1]
      print("Setting all LEDs to state {}".format(targetstate))
      self.__serialadapter.set_grid_led_all(targetstate)
    elif (messagepath.endswith("/led/set")):
      x = osc_arguments[1]
      y = osc_arguments[2]
      targetstate = osc_arguments[3]
      print("Setting LED {}, {} to state {}".format(x, y, targetstate))
    