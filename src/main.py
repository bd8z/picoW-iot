import json
import time

import machine
import network
import ubinascii
from umqtt.simple import MQTTClient

iot_core_endpoint = '{your-end-point}.amazonaws.com'
mqtt_topic ='dt/homeCtrl/tokyo/'
wifi_access_point = "{yourSSID}"
wifi_password = "{yourSSID-wifi_password}"

def getClientID():
    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
    return "picoW_" + mac

def get_ssl_params():
    keyfile = '/certs/private.der'
    with open(keyfile, 'rb') as f:
        key = f.read()
    certfile = "/certs/certificate.der"
    with open(certfile, 'rb') as f:
        cert = f.read()    
    ssl_params = {'key': key,'cert': cert, 'server_side': False}
    return ssl_params

def conncet_wifi():
    wlan = network.WLAN( network.STA_IF )
    wlan.active( True )
    time.sleep_ms(1000)
    retry = 10
    while retry >0:
        wlan.connect( wifi_access_point, wifi_password )
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep_ms(1000)
            print(".")
            timeout -= 1
        if not wlan.isconnected():
            print("not connected")
        if wlan.isconnected():
            print("connected")
            break
        retry -= 1

def read_sensor():
    sensor = machine.ADC(2)
    factor = 3.3 / 65535
    sensor_volt = sensor.read_u16() * factor
    return sensor_volt

def getBinaryMessage(value1):
    message = {}
    message["illuminance"] = value1
    data = json.dumps(message).encode()
    return data

# initialize
led = machine.Pin("LED", machine.Pin.OUT)
led.off()

# wifi connect
conncet_wifi()

ssl_params=get_ssl_params()
led.on()

# mqtt connect
mqtt_client_id = getClientID()
mqtt = MQTTClient( mqtt_client_id, iot_core_endpoint, port = 8883, keepalive = 10000, ssl = True, ssl_params = ssl_params )
mqtt.connect()

# send data
while True:
    try:
        led.on()
        for i in range(100):
            Msg = getBinaryMessage(read_sensor())
            print(Msg)
            mqtt.publish( topic = mqtt_topic + mqtt_client_id, msg = Msg , qos = 0 )
            time.sleep_ms(60*1000)
    except:
        led.off()
        conncet_wifi()
        try:
            mqtt.disconnect()
            time.sleep_ms(1000)
        except:
            pass     
        mqtt.connect()