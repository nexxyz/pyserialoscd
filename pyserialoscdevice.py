from pythonosc import dispatcher
import pyserialoscutils


# -----------
# Actions to queue for the serial communication
# -----------
class SerialAction:
    def __init__(self, actionname, *actionargs):
        self.actionname = actionname
        self.actionargs = actionargs

# -----------
# Each device will be represented by one endpoint
# -----------
class SerialOscDeviceEndpoint(pyserialoscutils.OscServerWrapper):
  def __init__(self, deviceid, devicetype, messageprefix = "/monome", size=[16, 8], destinationhost = "localhost", destinationport = 12222, rotation = 0):
    super().__init__(deviceid)
    self.id = deviceid
    self.type = devicetype
    self.messageprefix = messageprefix
    self.size = size
    self.destinationhost = destinationhost
    self.destinationport = destinationport
    self.rotation = rotation
    self.__actionqueue = []
    self.dispatcher.map("/sys/host", self.set_destination_host)
    self.dispatcher.map("/sys/port", self.set_destination_port)
    self.dispatcher.map("/sys/prefix", self.set_message_prefix)
    self.dispatcher.map("/sys/rotation", self.set_rotation)
    self.dispatcher.map("/info", self.get_info)
    self.dispatcher.map("/sys/info", self.get_info)

  def default_osc_handler(self, source, *osc_arguments):
    print("Processing device OSC command for device {}, Source: {}, Content {}".format(self.id, source, osc_arguments))
    self.__actionqueue.append(SerialAction(source, osc_arguments))

  def start(self, ip, port):
    super().start(ip, port)
  
  def stop(self):
    super().stop()

  # receiving messages
  def set_destination_port(self, requestpath, newport):
    print("new destination port for device {} requested - {}".format(self.id, newport))
    self.destinationport = newport

  def set_destination_host(self, requestpath, newhost):
    print("new host for device {} requested - {}".format(self.id, newhost))
    self.destinationhost = newhost

  def set_message_prefix(self, requestpath, newmessageprefix):
    print("new message prefix for device {} requested - {}".format(self.id, newmessageprefix))
    self.messageprefix = newmessageprefix

  def set_rotation(self, requestpath, newrotation):
    print("new rotation for device {} requested - {}".format(self.id, newrotation))
    self.rotation = newrotation

  def get_info(self, requestpath, destinationhost = "", destinationport = ""):
    print("info requested for device {} to targethost {} and targetport {}".format(self.id, destinationhost, destinationport))
    self.send_info(destinationhost, destinationport)

  # sending messages
  def send_prefix_message_to_destination(self, path, *osc_arguments):
    print("device {} sending message to destination with path {} and args {}".format(self.id, path, osc_arguments))
    pyserialoscutils.OscClientWrapper(self.destinationhost, self.destinationport).send_message(self.messageprefix + path, *osc_arguments)

  def send_message_to_destination(self, path, *osc_arguments):
    print("device {} sending message to destination with path {} and args {}".format(self.id, path, osc_arguments))
    pyserialoscutils.OscClientWrapper(self.destinationhost, self.destinationport).send_message(path, *osc_arguments)

  def send_message_to_specific_endpoint(self, host, port, path, *osc_arguments):
    print("device {} sending message to {}:{} with path {} and args {}".format(self.id, host, port, path, osc_arguments))
    # pyserialoscutils.OscClientWrapper(host, port).send_message(self.messageprefix + path, osc_arguments)
    pyserialoscutils.OscClientWrapper(host, port).send_message(path, *osc_arguments)

  def send_info(self, destinationhost = "", destinationport = ""):
    if(destinationhost == ""):
        destinationhost = self.destinationport
    if(destinationport == ""):
        destinationport = self.destinationport
    print("Device {} sending info with  targethost {} and targetport {}".format(self.id, destinationhost, destinationport))
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/id", self.id)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/size", self.size[0], self.size[1])
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/host", self.destinationhost)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/port", self.destinationport)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/prefix", self.messageprefix)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/rotation", self.rotation)

  def send_grid_key(self, x, y, state):
    print("Device {} sending key x {}, y {}, state {}".format(self.id, x, y, state))

  def send_tilt(self, n, x, y, z):
    print("Device {} sending tilt n {}, x {}, y {}, z {}".format(self.id, n, x, y, z))

  def send_arc(self, n, d):
    print("Device {} sending arc n {}, d {}".format(self.id, n, d))
  
  def send_enc(self, n, state):
    print("Device {} sending encoder n {}, state {}".format(self.id, n, state))
  