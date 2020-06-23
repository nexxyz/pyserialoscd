import signal
import time
from pythonosc import dispatcher
import pyserialoscutils

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

  testapplication_ip = "localhost"
  testapplication_port = 15555
  serialosc_ip = "localhost"
  serialosc_port = 12002
  device_ip = "localhost"
  device_port = 12235

  # Test Application
  testapplication = pyserialoscutils.OscServerWrapper("testapplication")
  testapplication.start(testapplication_ip, testapplication_port)

  print("Press CTRL-C to stop")
  pyserialoscutils.OscClientWrapper(serialosc_ip, serialosc_port).send_message(
      "/serialosc/list", "localhost", 15555)
  pyserialoscutils.OscClientWrapper(
      device_ip, device_port).send_message("/info", "localhost", 15555)

  while(True):
    pyserialoscutils.OscClientWrapper(device_ip, device_port).send_message(
        "/monome/grid/led/set", 5, 7, 1)
    time.sleep(2)
    pyserialoscutils.OscClientWrapper(device_ip, device_port).send_message(
        "/monome/grid/led/set", 5, 7, 0)
    time.sleep(2)
