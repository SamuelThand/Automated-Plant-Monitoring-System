"""
Library for connecting to wlan and mqtt
"""

import machine
from network import WLAN  # Pycom driver class for the WiFi network processor
from robust2 import MQTTClient

wlan = WLAN(mode=WLAN.STA)


def wlan_connect(wlan_ssid: str, wlan_password: str) -> None:
    """Connect to a wlan access point with WPA2 encryption"""

    if wlan.isconnected():
        print('WLAN is connected.')
        return

    wlan.connect(ssid=wlan_ssid, auth=(WLAN.WPA2, wlan_password))

    print('Connecting to WLAN...')
    while not wlan.isconnected():
        machine.idle()

    print('Connected to WLAN. Interface config:')
    print('Local IP          Netmask         Gateway          DNS')
    print(wlan.ifconfig())


def adafruit_connect(adafruit_user: str, adafruit_key: str):
    """Connect to Adafruit"""

    def sub_cb(topic, message, retained, duplicate):
        print((topic, message, retained, duplicate))

    mqtt_client = MQTTClient('LoPy4', "io.adafruit.com",
                             port=1883, user=adafruit_user,
                             password=adafruit_key)

    mqtt_client.DEBUG = True
    mqtt_client.KEEP_QOS0 = False
    mqtt_client.NO_QUEUE_DUPS = True
    mqtt_client.MSG_QUEUE_MAX = 2
    mqtt_client.set_callback(sub_cb)

    print('Connecting to Adafruit...')
    mqtt_client.connect()
    mqtt_client.subscribe(b'YOUR_ADAFRUIT_USERNAME/feeds/plant-system')

    return mqtt_client
