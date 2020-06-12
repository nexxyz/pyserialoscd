# pyserialoscd
A simplified, python-based serialoscd implementation

## What it does
Right now, the main grid functionalities are there. I have tested it with my neotrellis-monome using "Monome Home.maxpat". Almost everything works, only the "map test" using "vari-bright" is buggy. 

It also supports, in theory, multiple devices. I have not implemented anything around tilt, arc or other devices than grids (yet - if there's demand I might do that). I am sure if it works with grids that are not 16x8.

## How to run it
First you need pyserial and python-osc:

    python -m pip install pyserial python-osc

Then just check out this repo (you need to have git installed):

    git clone https://github.com/nexxyz/pyserialoscd.git

Then go to that folder and run pyserialoscd by executing:

    python pyserialoscd --serial <your serial port, e.g. "COM3" or "/dev/ttyUSB2">

You can also add more than one serial port, but this is untested. You can stop it using CTRL-C (not CTRL-Z).

For help in case anything goes wrong, just call

    python pyserialoscd --help

## Why another serialoscd implementation?
I started to make this to use my neotrellis-monome by okeyron (see https://github.com/okyeron/neotrellis-monome). Due to the windows version of serialosc requiring an FTDI device to find it in the Windows registry, e.g. teensy-based devices that don't use FTDI drivers are not picked up by serialoscd.

And for fun.