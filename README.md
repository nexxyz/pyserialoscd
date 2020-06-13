# pyserialoscd

A simplified, python-based serialoscd implementation

## What it does

Right now, the main grid functionalities are there. I have tested it with my neotrellis-monome using "Monome Home.maxpat". It can be used as a replacement for serialoscd, as long as you don't need any of the more low-level functionalities (such as setting a device ID). It currently allows to set and stores rotation information, but does not do anything with that info.

It also supports multiple devices, but this has not been tested by me. I have not implemented anything around tilt, arc or other devices than grids (yet - if there's demand I might do that). I am sure if it works with grids that are not 16x8.

**Note:** It seems, at least on Windows, the /grid/map/level (and possibly row & col) OSC command (when tested with monome home's vari-bright map-test) does not behave at expected with okeyron's original firmware. Please use [my modified firmware](https://github.com/nexxyz/neotrellis_monome_teensy) instead. It also adds variable intensity for mono-bright applications using the /grid/intensity OSC command.

## How to install it

You need to download and install a recent version of [python](python.org/downloads/).

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

## Why another serialoscd implementation

I started to make this to use my neotrellis-monome by okeyron (see [this thread](https://github.com/okyeron/neotrellis-monome)). Due to the windows version of serialosc requiring an FTDI device to find it in the Windows registry, e.g. teensy-based devices that don't use FTDI drivers are not picked up by serialoscd.

And for fun.
