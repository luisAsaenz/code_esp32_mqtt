# import modules
# Derived from: 
# * https://github.com/peterhinch/micropython-async/blob/master/v3/as_demos/auart.py
# * https://github.com/tve/mqboard/blob/master/mqtt_async/hello-world.py
# * https://github.com/peterhinch/micropython-mqtt
# * https://github.com/embedded-systems-design/external_pycopy-lib


import ssl

from mqtt_as.mqtt_as import MQTTClient
from mqtt_as.mqtt_local import wifi_led, blue_led, config
import uasyncio as asyncio
from config import *
from machine import UART
from machine import Pin
import time


MAX_MESSAGE_LEN=64
team = [b'a',b'b',b'c',b'd']
id = b'b' #tyler - c , alex - a, frank - d
broadcast = b'X'

# initialize a new UART class
uart = UART(2, 9600,tx=17,rx=16)
# run the init method with more details including baudrate and parity
uart.init(9600, bits=8, parity=None, stop=1) 
# define pin 2 as an output with name led. (Pin 2 is connected to the ESP32-WROOM dev board's onboard blue LED)
buttondebug = Pin(25,Pin.IN, Pin.PULL_UP) # Button to SEND MESSAGE to MQTT broker
led = Pin(19,Pin.OUT) #change LED from 2

sensor_val_state = [0, 0]

sensor_state = {
    '1': 0,
    '2': 0
}
topic_subscribed = {
    'SUB' : 0,
    'RPM' : 0
}
topic_message = {
    'SUB' : b'',
    'RPM' : b''
}
last_msg = {
    'RPM' : b''
}
MAXTX = 4
received_sv = 0
token = 0



def send_message(message):
    # if len(message)>MAX_MESSAGE_LEN:
    #     print('ESP: message too long')
    #     return
    if message[0:2] != b'AZ':
        print('ESP: message does not start with AZ')
        return
    if message[-2:] != b'YB':
        print('ESP: message does not end with YB')
        return
    if message[2:3] not in team:
        print('ESP: sender not in team')
        return
    if message[3:4] not in team:
        if message[3:4] == broadcast:
            print(f'ESP: sending broadcast message ---> {message}')
            uart.write(message)

            pass
            
        else:
            print('ESP: receiver not in team')
        return
    
    if message[2:3] == id:
        uart.write(message)
        print('ESP: sending MY message ', message)
    else:
        uart.write(message)
        print('ESP: sending team message ', message)



    # send_queue.append(message)
async def sb_cb_msghandler():
    while True:
        await asyncio.sleep_ms(10)
        topic_rv_msg = ''
        for k in list(topic_subscribed.keys()):
            if topic_subscribed[k] == 1:
                topic_rv_msg = k
                break

        if topic_rv_msg is not '':
            # send message to frank
            topic_subscribed[topic_rv_msg] = 0
            msg = topic_message.get(topic_rv_msg, b'TOPIC NOT IN DICTIONARY')
            print(topic_rv_msg)
            print(msg)

            try:
                s = b''
                if msg[-1:] != b';':
                    msg = b'End message in ";"'
                    if topic_rv_msg == 'SUB':
                        await client.publish(TOPIC_PUB, msg, qos=1)
                    else: 
                        last_msg[topic_rv_msg] = msg
                        await client.publish(TOPIC_RPM, msg, qos=1)
                    #print('End message in ";"') #debug
                else:
                    if topic_rv_msg == 'SUB':
                        if len(msg) > 2 or len(msg) < 2:
                            s = str('Entry too ' + ('long' if len(msg)>2 else 'short') + '. Here is an example, 2;')   
                            await client.publish(TOPIC_PUB, s.encode(), qos=1)
                            topic_subscribed[topic_rv_msg] = 0   

                            continue
                        else:
                            if msg[0:1] not in b'012':
                                if type(msg[0:1]) != bytearray:
                                    await client.publish(TOPIC_PUB, b'Use regular characters when entering values. Try values: 0, 1, 2. Followed by ";"', qos=1)
                                    topic_subscribed[topic_rv_msg] = 0
                                    continue
                                else:
                                    await client.publish(TOPIC_PUB, b'Entry unaccepted. Try values: 0, 1, 2. Followed by ";"', qos=1)
                                    topic_subscribed[topic_rv_msg] = 0

                                    continue
                    #now that error handling is done. we check once again if msg is in index of acceptable values
                            else:                    # can possibly get rid of if statement since we 
                                s = b'AZbd'+ msg[0:1] + b'YB'     # check previously if id and value are in acceptable range
                                send_message(s)
                                s = 'Motor is set to: {}'.format(msg[0:1].decode())


                                await client.publish(TOPIC_PUB, s.encode(), qos=1)

                                s=b''

                    elif topic_rv_msg == 'RPM':
                        try:
                            target_RPM = int(msg[0:-1])
                            print(f"this is target RPM: {target_RPM}")
                            if target_RPM > 100 or target_RPM < 0:
                                if target_RPM > 100:
                                    s = f'Entry, {target_RPM}, unaccepted, too large. Try a value between 0 and 100;'
                                    #await client.publish(TOPIC_RPM, s.encode(), qos=1)
                                else:
                                    s = f'Entry, {target_RPM}, unaccepted, not large enough. Try a value between 0 and 100;'

                                    #await client.publish(TOPIC_RPM, s.encode(), qos=1)
                            elif len(msg) < 2 or len(msg) > 4:
                                s = 'Message is too, ' + 'short;' if len(msg) < 2 else 'long;'
                            else:
                                s = f'Setting RPM to: {target_RPM};'
                                print(s)
                                # send message to Tyler
                                #await client.publish(TOPIC_RPM, s.encode(), qos=1)
                        except ValueError:
                            s = 'Entry unaccepted. Value has to be a number;'
                            #await client.publish(TOPIC_RPM, s.encode(), qos=1)
                        s= str(s)
                        last_msg[topic_rv_msg] = s.encode()
                        await client.publish(TOPIC_RPM, s.encode(), qos=1)
            
            except IndexError:
                pass


def handle_message(message):
    my_string = message.decode('utf-8')
    if message[3:4] != id and message[3:4] != broadcast: ## checks if receiver is not my id or the broadcast
       
        print(f'ESP: handling team message {message}')
        send_message(message)
    else:
        # if broadcast message and message type is 8 then pass message if not handle message normally then pass broadcast
        message_type = message[4]
        if message[3:4] == broadcast and message_type == 8:
            print('ESP: passing broadcast ', message)
            send_message(message)
        else: 
            if message[3:4] == broadcast:
                print('ESP: handling broadcast ', message)
            else:
                print(f'ESP: handling my message {message}')
            if message_type == 2:
                # Handle message type 2
                sensor_value = message[5]
                if sensor_value > 100:
                    print('ESP: sensor value is too out of range')
                    sensor_value = 0
                else:
                    print(f'ESP: message contains sensor value: {sensor_value}')
                    sensor_val_state[0] = sensor_value
                    sensor_val_state[1] = 1            

            elif message_type == 5:
                # Handle message type 5
                subsystem_id = my_string[5]
                if subsystem_id in team.decode('utf-8'):
                    print(f'ESP: subsystem {subsystem_id} that is experiencing error')
                else:
                    print(f'ESP: Subsystem, {subsystem_id} is not in team.')
                pass

            elif message_type == 6:
                # Handle message type 6
                motor_status = message[5]
                if motor_status == 0:
                    print('ESP: Motor is not down.')
                elif motor_status == 1:
                    print('ESP: Motor is up.')
                else: 
                    print('ESP: Motor status is unknown.')

            elif message_type == 7:
                # Handle message type 7
                sensor_status = message[5]
                if sensor_status == 0:
                    print('ESP: Sensor is not down.')
                elif sensor_status == 1:
                    print('ESP: Sensor is up.')
                else: 
                    print('ESP: Sensor status is unknown.')
                pass

            else:
                print('ESP: unknown message type.')
            if message[3:4] == broadcast:
                print('ESP: broadcast messaged handled, passing broadcast.')
                send_message(message)
            else:
                print(f'ESP: Message, {message} ,  handled. Deleting message..')  

    


async def process_rx():

    # stream = []
    stream = b''
    message = b''
    send_queue = []
    receiving_message=False

    while True:
        # read one byte
        c = uart.read(1)
        # if c is not empty:
        
            
        if c is not None:
            
            stream+=c
            try:
                if stream[-2:]==b'AZ':
                    # print('ESP: message start:')
                    message=stream[-2:-1] #add a to message
                    receiving_message=True
            except IndexError:
                pass
            try:
                if stream[-2:]==b'YB':
                    if receiving_message == False:
                        message=b''
                        pass
                    else:
                        message+=stream[-1:]
                        receiving_message = False
                        print('ESP: message received:',message)
                        handle_message(message)
                    stream=b''

                    led.value(led.value()^1)
            
            except IndexError:
                pass
            #try:
            #   this will handle incoming messages that are from MQTT
            #except IndexError:
            #    pass
            if receiving_message:
                
                message+=c #immediately after receiving_message == true, Z is added to message
                #print(message) 
                #print(c)


                if len(message)==3:
                    if  (message[2:3] not in team):
                        print('ESP: sender not in team ------>  ')
                        print(c)

                        # get rid of message if sender not on team
                       # message=b''
                        receiving_message = False
                    else:
                        if message[2:3] == id:
                            print('ESP: receiving message from self. DELETING...')
                          #  message=b''
                            receiving_message = False
                        else:
                            print('ESP: sender in team')

                if len(message)==4:
                    if  (message[3:4] not in team):
                        
                        # get rid of message if sender not on team
                        #message=b''
                        if message[3:4] == broadcast:
                            print('ESP: receiving broadcast')
                        else:
                            print('ESP: receiver not in team')
                            receiving_message = False
                    else:
                        print('ESP: receiver in team')

                if len(message)>MAX_MESSAGE_LEN:
                    receiving_message = False
                    print('ESP: Message too long, aborting')
                    message=b''


        await asyncio.sleep_ms(10)    




async def readingButton():
    laststate = 0
    try:
        while True:
            await asyncio.sleep_ms(50)

            current_state = buttondebug.value()
            if current_state != laststate:
                #print("Button Pressed")
                laststate = current_state
                if current_state == 0:
                    uart.write(b'button pressed;')
                laststate = current_state
            await asyncio.sleep_ms(20)
    except: 
        pass


# Subscription callback
def sub_cb(topic, msg, retained):
    

    print(f'Topic: "{topic.decode()}" Message: "{msg.decode()}" Retained: {retained}')
    if topic.decode()[-3:] == 'SUB':
        if msg.decode() == "h;\n" and topic_subscribed['SUB'] == 0:
            pass
        else:
            topic_message[topic.decode()[-3:]] = msg
            topic_subscribed[topic.decode()[-3:]] = 1
    elif topic.decode()[-3:] == 'RPM':
        if last_msg[topic.decode()[-3:]] != msg:
            topic_message[topic.decode()[-3:]] = msg
            topic_subscribed[topic.decode()[-3:]] = 1



async def sensor_update():
    while True:
        await asyncio.sleep_ms(100)
        if (sensor_val_state[1] == 0):
            sensor_vals = 'The RPM at the bottom gate: Sensor not connected.'
        else:
            sensor_vals = 'The RPM at the bottom gate: {} RPM;'.format(sensor_val_state[0])
         

        await client.publish(TOPIC_SENSOR, sensor_vals.encode(), qos=1)


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

    
    await client.subscribe(TOPIC_RPM, 1)
   




async def main(client):
    try:
        await client.connect()

        s = b'Enter a value in SUB to change gate position. Values accepted: 0  1  2'
        await client.publish(TOPIC_PUB, s, qos = 1)

        s = b'RPM at bottom gate. Enter a value between 0 and 100:  '
        last_msg['RPM'] = s
        await client.publish(TOPIC_RPM, s, qos=1)

    except OSError:
        print('Connection failed.')
        return
    ##asyncio.create_task(process_rx())
    asyncio.create_task(readingButton())
    asyncio.create_task(sensor_update())
    asyncio.create_task(sb_cb_msghandler())



    n = 0
    while True:
        await asyncio.sleep(5)
        print('publish', n)
        # If WiFi is down the following will pause for the duration.
        await client.publish(TOPIC_HB, '{} {}'.format(n, client.REPUB_COUNT), qos = 1)

        n += 1
    #counter = 0

    #while True:
    #    token = counter%100
    #    
    #    if token == 9: # MESSAGE TYPE1
    #        message = b'AZcd\x0130dfdsgrejhv dfjhgdlkfjhvldkfj fjklhguieoeh dfhuigb dfjfdgfdgsdfgdfgdffYB'
    #        send_message(message)
    #
    #    if token == 11: # MESSAGE TYPE3
    #        message = b'AZbX\x03wifi is not communicatingYB'       
    #        send_message(message)
#
    #    if token == 15: # MESSAGE TYPE2
    #        message = b'AZcb\x021\x10YB'
    #        send_message(message)
#
    #    if token == 22: # MESSAGE TYPE6
    #        message = b'AZcX\x08this is broadcastYB'
    #        send_message(message)

        # if token == 40: # MESSAGE TYPE4
        #     message = b'AZcb\x040YB'
        #     send_message(message)

        # if token ==  45: # MESSAGE TYPe5
        #     message = b'AZbd\x05bYB'
        #     send_message(message)

        # if token == 50: # MESSAGE TYPe8
        #     message = b'AZcX\x08this is the broadcastYB'
        #     send_message(message)
        

        #counter += 1
        #await asyncio.sleep(1)

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
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

asyncio.create_task(process_rx()) #if don't work remove and add to main function
asyncio.create_task(heartbeat())

try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
    asyncio.new_event_loop()





