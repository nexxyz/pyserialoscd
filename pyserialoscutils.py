from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc.udp_client import SimpleUDPClient
from threading import Thread

# -----------
# To make it a bit easier to send osc messages
# -----------
class oscclient_wrapper:
  def __init__(self, targetip, targetport):
    super().__init__()
    self.targetip = targetip
    self.targetport = targetport
    self.client = SimpleUDPClient(targetip, targetport)  # Create client
  
  def send_message(self, address, *osc_arguments):
    print("Sending message to {}:{} with path {} and data {}".format(self.targetip, self.targetport, address, osc_arguments))
    self.client.send_message(address, osc_arguments)

# -----------
# For easy starting and stopping of oscservers
# -----------
class oscserver_wrapper:
  def __init__(self, friendlyname):
    super().__init__()
    self.friendlyname = friendlyname
    self.dispatcher = dispatcher.Dispatcher()
    self.dispatcher.set_default_handler(self.default_osc_handler, self)
  
  def default_osc_handler(self, source, *osc_arguments):
    print("WARNING: Unhandled OSC message received. Source: {}, Content {}".format(source, osc_arguments))

  def start(self, ip, port):
    self.server = osc_server.BlockingOSCUDPServer((ip, port), self.dispatcher)
    print("Starting OSC server {} on: {}".format(self.friendlyname, self.server.server_address))
    self.server_thread = Thread(target = self.server.serve_forever)
    self.server_thread.start()
      
  def stop(self):
    print("Stopping OSC server: {}".format(self.friendlyname))
    self.server.shutdown()
    self.server_thread.join()