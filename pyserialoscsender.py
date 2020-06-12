import pyserialoscutils

# -----------
# We will need to send osc to the target
# -----------
class SerialOscDeviceMessageSender():
  def __init__(self, messageprefix, destinationhost, destinationport):
    super().__init__()
    self.messageprefix = messageprefix
    self.destinationhost = destinationhost
    self.destinationport = destinationport

  # sending messages
  def send_prefix_message_to_destination(self, path, *osc_arguments):
    pyserialoscutils.OscClientWrapper(self.destinationhost, self.destinationport).send_message(self.messageprefix + path, *osc_arguments)

  def send_message_to_destination(self, path, *osc_arguments):
    pyserialoscutils.OscClientWrapper(self.destinationhost, self.destinationport).send_message(path, *osc_arguments)

  def send_message_to_specific_endpoint(self, host, port, path, *osc_arguments):
    pyserialoscutils.OscClientWrapper(host, port).send_message(path, *osc_arguments)

  def send_info(self, id, sizex, sizey, rotation, destinationhost = "", destinationport = ""):
    if(destinationhost == ""):
        destinationhost = self.destinationport
    if(destinationport == ""):
        destinationport = self.destinationport
    print("Sending info with  targethost {} and targetport {}".format(destinationhost, destinationport))
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/id", id)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/size", sizex, sizey)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/host", self.destinationhost)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/port", self.destinationport)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/prefix", self.messageprefix)
    self.send_message_to_specific_endpoint(destinationhost, destinationport, "/sys/rotation", rotation)

  def send_grid_key(self, x, y, state):
    print("Device with prefix {} sending key x {}, y {}, state {}".format(self.messageprefix, x, y, state))
    self.send_prefix_message_to_destination("/grid/key", x, y, state)

  def send_tilt(self, n, x, y, z):
    print("Device with prefix {} sending tilt n {}, x {}, y {}, z {}".format(self.messageprefix, n, x, y, z))

  def send_arc(self, n, d):
    print("Device with prefix {} sending arc n {}, d {}".format(self.messageprefix, n, d))
  
  def send_enc(self, n, state):
    print("Device with prefix {} sending encoder n {}, state {}".format(self.messageprefix, n, state))
