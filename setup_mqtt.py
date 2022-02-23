#Complete project details at https://RandomNerdTutorials.com

import os
import time
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()

ssid = 'senor_fiddle_biscuits'
password = '6503531241'

#ssid = 'photon'
#password = 'particle' 

station = network.WLAN(network.STA_IF)

station.active(True)
if not station.isconnected():
    station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())


import upip
if 'lib' in os.listdir('./'):
    if 'logging.py' not in os.listdir('lib/'):
        upip.install('micropython-logging')
        upip.install('micropython-mqtt')
else:
    upip.install('micropython-logging')
    upip.install('micropython-mqtt')


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(station.ifconfig())