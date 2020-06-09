import signal
import time
from pythonosc import dispatcher
import pyserialoscutils

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
    print("Stopping testapp")
    testapplication.stop()
    exit(0)

# -----------
# Main entry point
# -----------
if __name__ == "__main__":
  signal.signal(signal.SIGINT, keyboardInterruptHandler)

  testapplication_ip = "127.0.0.1"
  testapplication_port = 17777
  serialosc_ip = "127.0.0.1"
  serialosc_port = 12002

  # Test Application
  testapplication = pyserialoscutils.oscserver_wrapper("testapplication")
  testapplication.start(testapplication_ip, testapplication_port)
  
  print("Press CTRL-C to stop")
  while True:
    pyserialoscutils.oscclient_wrapper(serialosc_ip, serialosc_port).send_message("/serialosc/list", "127.0.0.1", 17777)
    time.sleep(1)