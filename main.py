# Derived from: 
# * https://github.com/peterhinch/micropython-async/blob/master/v3/as_demos/auart.py
# * https://github.com/tve/mqboard/blob/master/mqtt_async/hello-world.py
# * https://github.com/peterhinch/micropython-mqtt
# * https://github.com/embedded-systems-design/external_pycopy-lib


import ssl

from mqtt_as.mqtt_as import MQTTClient
from mqtt_as.mqtt_local import wifi_led, blue_led, config
import uasyncio as asyncio
from machine import UART
import time
import logging
logging.basicConfig(level=logging.DEBUG)
from config import *

my_id = b'a'
team = b'abcd'
broadcast = b'z'

MAXTX = 4

uart = UART(2, 9600,tx=17,rx=16)
uart.init(9600, bits=8, parity=None, stop=1,flow=0) # init with given parameters


def send_message(message):
    print('send message')
    # send_queue.append(message)

def fun7(message):
    print('Saw an H')

def fun3(message):
    print('I am fun3')

def handle_message(message):
    if message[2:3]==my_id:
        print('from me')
        pass #do nothing with it, it was not received
    if message[3:4]==my_id:
        print('to me')
        handle_my_message(message)
    elif message[3:4]==broadcast:
        print('broadcast')
        handle_my_message(message)
        send_message(message)
    else:
        print('to someone else')
        send_message(message)

def handle_my_message(message):
    # print('handle_my_message')
    if message[4:5]==b'H':
        # print('handle function 7')
        fun7(message)
    

async def receiver():
    buffer = b'\x00\x00\x00\x00'
    sreader = asyncio.StreamReader(uart)
    message_incoming=False
    while True:
        c=await sreader.read(1)
        # print(c)
        buffer+=c
        while  len(buffer)>4:
            buffer=buffer[1:]
        if buffer[-2:]==b'AZ':
            message=b''
            message+=buffer[-2:-1]
            message_incoming=True
        if message_incoming:
            if buffer[-2:]==b'YB':
                message+=buffer[-1:]
                handle_message(message)
                await client.publish(TOPIC_PUB, message, qos=1)
                print('published', message)
                message_incoming=False
            else:
                message+=buffer[-1:]
                if len(message)==3:
                    if message[-1:]==my_id:
                        print('message from me')
                if len(message)==4:
                    if message[-1:]==my_id:
                        print('message to me')
                    elif message[-1:]==broadcast:
                        print('message to all')
# Subscription callback
def sub_cb(topic, msg, retained):

    print(f'Topic: "{topic.decode()}" Message: "{msg.decode()}" Retained: {retained}')

    uart.write(msg)
    # uart.write('\r\n')
    # time.sleep(.01)


# Demonstrate scheduler is operational.
async def heartbeat():
    s = True
    while True:
        await asyncio.sleep_ms(500)
        blue_led(s)
        s = not s

async def wifi_han(state):
    wifi_led(not state)
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe(TOPIC_SUB, 1)

async def main(client):
    try:
        await client.connect()
        print('Connection established.')
    except OSError:
        print('Connection failed.')
        return
    asyncio.create_task(receiver())

    n = 0
    while True:
        await asyncio.sleep(5)
        # print('publish', n)
        # If WiFi is down the following will pause for the duration.
        await client.publish(TOPIC_HB, '{} {}'.format(n, client.REPUB_COUNT), qos = 1)
        n += 1

# Define configuration

config['server'] = MQTT_SERVER
config['ssid']     = WIFI_SSID
config['wifi_pw']  = WIFI_PASSWORD

config['ssl']  = True
# read in DER formatted certs & user key
with open('certs/student_key.pem', 'rb') as f:
    key_data = f.read()
with open('certs/student_crt.pem', 'rb') as f:
    cert_data = f.read()
with open('certs/ca_crt.pem', 'rb') as f:
    ca_data = f.read()
ssl_params = {}
ssl_params["cert"] = cert_data
ssl_params["key"] = key_data
ssl_params["cadata"] = ca_data
ssl_params["server_hostname"] = MQTT_SERVER
ssl_params["cert_reqs"] = ssl.CERT_REQUIRED
config["time_server"] = MQTT_SERVER
config["time_server_timeout"] = 10

config['ssl_params']  = ssl_params

config['subs_cb'] = sub_cb
config['wifi_coro'] = wifi_han
config['connect_coro'] = conn_han
config['clean'] = True
config['user'] = MQTT_USER
config["password"] = MQTT_PASSWORD

# Set up client
MQTTClient.DEBUG = False  # Optional
client = MQTTClient(config)

asyncio.create_task(heartbeat())
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
    asyncio.new_event_loop()





