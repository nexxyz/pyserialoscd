# pyserialoscd

> **⚠️ Untested:** The latest changes (rotation support, serialosc compatibility fixes, standard vari-bright protocol) have not been tested on hardware yet. Firmware and pyserialoscd must be updated together, as the serial protocol changed.
> Last stable versions: [neotrellis_monome_teensy](https://github.com/nexxyz/neotrellis_monome_teensy/tree/898ff18d4dbc19901a527cd97102ca7632c30869) and [pyserialoscd](https://github.com/nexxyz/pyserialoscd/tree/580b5ac89caa787ccd0d50803da273f81f6907f6).

A simplified, python-based serialoscd implementation

## What it does

It should work with most standard monome-grid applications. I have tested it with my neotrellis-monome using "Monome Home.maxpat". It can be used as a replacement for serialoscd, as long as you don't need any of the more low-level functionalities (such as setting a device ID). Rotation (/sys/rotation 0, 90, 180 or 270) is supported and follows the conventions of the original serialosc: key presses and all led commands are translated, and /sys/size reports the rotated size.

It also supports multiple devices, but this has not been tested by me. I have not implemented anything around tilt, arc or other devices than grids (yet - if there's demand I might do that). I am sure if it works with grids that are not 16x8.

**Note:** Vari-bright map/row/col levels are sent like the original serialosc does (two 4-bit levels per byte). Please use [my modified firmware](https://github.com/nexxyz/neotrellis_monome_teensy), which reads this format, waits for messages split across USB packets and ignores leds outside the grid. It also adds variable intensity for mono-bright applications using the /grid/intensity OSC command.

## How to install it

You need to download and install a recent version of [python](python.org/downloads/), at least version 3.5.

Then you need pyserial and python-osc, which you can install using this command:

    python -m pip install pyserial python-osc

Then just check out this repo (you need to have git installed):

    git clone https://github.com/nexxyz/pyserialoscd.git

Or you could just [download this repo as a ZIP](https://github.com/nexxyz/pyserialoscd/archive/master.zip) and extract it.

## How to use it

After you have set everything up, go to that folder and run pyserialoscd by executing:

    python pyserialoscd

It is listening at the same port as serialoscd by default, so please make sure it is not running or specify an alternative port using the *--serialoscport* parameter.

It also assumes that all devices connected to a serial port are monome grids. If that is not the case, you can blacklist unwanted ports using the *nottheseserialports* parameter, e.g.:

    python pyserialoscd --nottheseserialports COM10 COM12

There is also the inverse *--onlytheseserialports* parameter if you really only want to detect devices on specific ports.

For help in case anything goes wrong, just call

    python pyserialoscd --help

Like serialosc, pyserialoscd remembers the OSC port, application host/port, prefix and rotation of each device (by device id), so a device keeps its port between runs. The settings are stored as JSON in `%LOCALAPPDATA%\pyserialoscd` on Windows and `~/.config/pyserialoscd` elsewhere; use *--configdir* to choose another folder. New devices start with the serialosc defaults (prefix /monome, application port 8000).

Serial ports that do not answer like a monome grid within a second are ignored until they are plugged in again. If several devices report the same id, a suffix is added (e.g. neo-monome-2) - better give each grid its own id in the firmware.

## Why another serialoscd implementation

I started to make this to use my neotrellis-monome by okeyron (see [this thread](https://github.com/okyeron/neotrellis-monome)). Due to the windows version of serialosc requiring an FTDI device to find it in the Windows registry, e.g. teensy-based devices that don't use FTDI drivers are not picked up by serialoscd.

And for fun.

## Further plans
I am extending this as I need and/or feel like it. If you would find additional functionality useful, e.g. monome-arc support, low-level commands such as setting device ID, or if you find very annoying bugs, let me know. Also, if anyone tests it with multiple grids, or on other platforms, I'm quite interested to hear about your results.  
