# Copyright © 2020 by Thorsten von Eicken.
from mqtt_async import MQTTClient, config
import uasyncio as asyncio
import time

MAXTX = 4


#import uasyncio as asyncio
from machine import UART
uart = UART(2, 9600,tx=17,rx=16)
uart.init(9600, bits=8, parity=None, stop=1,flow=0) # init with given parameters


import logging
logging.basicConfig(level=logging.DEBUG)

# Change the following configs to suit your environment
TOPIC           = 'EGR314/Team321/ABC'
config.server   = 'egr314.ddns.net' # can also be a hostname

config.ssid     = 'photon'
config.wifi_pw  = 'particle'

# swriter = asyncio.StreamWriter(uart, {})

async def sender():
   swriter = asyncio.StreamWriter(uart, {})
   while True:
       swriter.write(b'Hel\n')
       await swriter.drain()
       await asyncio.sleep(1)

async def receiver():
    b = b''
    sreader = asyncio.StreamReader(uart)
    while True:
        res = await sreader.read(1)
        if res==b'\n':
            await client.publish(TOPIC, b, qos=1)
            print('published', b)
            b = b''
        else:
            b+=res
            #print('Recieved', res)

def callback(topic, msg, retained, qos):
    print('callback',topic, msg, retained, qos)
    while (not not msg):
        
#         swriter.write(msg[:4])
#         await swriter.drain()
#         msg = msg[4:]
#         await asyncio.sleep(.1)
        uart.write(msg[:MAXTX])
        time.sleep(.01)
        msg = msg[MAXTX:]
    uart.write('\r\n')
    time.sleep(.01)
        
    
    

async def conn_callback(client): await client.subscribe(TOPIC, 1)

async def main(client):
    asyncio.create_task(receiver())
    #asyncio.create_task(sender())
    await client.connect()
    n = 0
    while True:
        #print('publish', n)
        #await client.publish(TOPIC, 'Hello World #{}!'.format(n), qos=1)
        await asyncio.sleep(1)
        #n += 1

config.subs_cb = callback
config.connect_coro = conn_callback

client = MQTTClient(config)
loop = asyncio.get_event_loop()
loop.run_until_complete(main(client))
