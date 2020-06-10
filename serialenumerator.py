from __future__ import absolute_import

import sys
import os

# chose an implementation, depending on os
#~ if sys.platform == 'cli':
#~ else:
if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
#~ elif os.name == 'java':
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))


def list_ports():
    portlist = []
    for port in sorted(comports(include_links=True)):
        portlist.append(port.device)

    return portlist

print(list_ports())