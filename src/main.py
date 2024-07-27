import json
import ssl
import time

import machine
import network
import ntptime
import ubinascii
from umqtt.simple import MQTTClient

iot_core_endpoint = "{your-end-point}.amazonaws.com"
mqtt_topic = "dt/homeCtrl/tokyo/"
wifi_access_point = "{yourSSID}"
wifi_password = "{yourSSID-wifi_password}"


def getClientID():
    mac = ubinascii.hexlify(network.WLAN().config("mac"), ":").decode()
    return "picoW_" + mac


def get_ssl_context():
    keyfile = "/certs/private.der"
    certfile = "/certs/certificate.der"
    cafile = "/certs/routeca.der"

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(cafile=cafile)
    context.load_cert_chain(certfile, keyfile)
    return context


def conncet_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep_ms(1000)
    wlan.active(True)
    time.sleep_ms(3000)
    retry = 10
    while retry > 0:
        wlan.connect(wifi_access_point, wifi_password)
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

ntptime.settime()
ssl_context = get_ssl_context()
led.on()

# mqtt connect
mqtt_client_id = getClientID()
mqtt = MQTTClient(
    mqtt_client_id, iot_core_endpoint, port=8883, keepalive=10000, ssl=ssl_context
)
mqtt.connect()

# send data
while True:
    try:
        led.on()
        for i in range(100):
            Msg = getBinaryMessage(read_sensor())
            print(Msg)
            print(mqtt_topic + mqtt_client_id)
            mqtt.publish(topic=mqtt_topic + mqtt_client_id, msg=Msg, qos=0)
            time.sleep_ms(60 * 1000)
    except:
        led.off()
        conncet_wifi()
        try:
            mqtt.disconnect()
            time.sleep_ms(1000)
        except:
            pass
        mqtt.connect()
