from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc.udp_client import SimpleUDPClient
from threading import Thread

# -----------
# To make it a bit easier to send osc messages
# -----------
class OscClientWrapper:
  def __init__(self, targetip, targetport):
    super().__init__()
    self.targetip = map_localhost_to_ip4(targetip)
    self.targetport = targetport
    self.__client = SimpleUDPClient(self.targetip, self.targetport)  # Create client
  
  def send_message(self, address, *osc_arguments):
    print("Sending message to {}:{} with path {} and data {}".format(self.targetip, self.targetport, address, *osc_arguments))
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
  
  def default_osc_handler(self, source, *osc_arguments):
    print("WARNING: Unhandled OSC message received by {}. Source: {}, Content {}".format(self.friendlyname, source, osc_arguments))

  def start(self, host, port):
    self.host = map_localhost_to_ip4(host)
    self.port = port
    self.__server = osc_server.BlockingOSCUDPServer((self.host, self.port), self.dispatcher)
    print("Starting OSC server {} on: {}".format(self.friendlyname, self.__server.server_address))
    self.__server_thread = Thread(target = self.__server.serve_forever)
    self.__server_thread.start()
      
  def stop(self):
    print("Stopping OSC server: {}".format(self.friendlyname))
    self.__server.shutdown()
    self.__server_thread.join()

def map_localhost_to_ip4(host):
    if (host == "localhost"):
        return "127.0.0.1"
    else:
        return host