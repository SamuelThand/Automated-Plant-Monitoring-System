"""
Main program for the plant monitoring system
"""

import pycom
import time
from machine import Pin, ADC, sleep
import connections
import keys
import json
from dht import DTH

start_setup = time.time()

adc = ADC()
adc2 = ADC(bits=10)

# Temperature sensor
temp_sensor = adc.channel(pin='P16')

# Light sensor
light_sensor_pin = Pin('P17', mode=Pin.IN)
light_sensor = adc2.channel(pin='P17', attn=ADC.ATTN_11DB)

# Soil moisture sensor
moisture_sensor_power = Pin('P10', mode=Pin.OUT, pull=Pin.PULL_DOWN)
soil_moisture_sensor = adc.channel(pin='P18', attn=ADC.ATTN_11DB)

# Air humidity sensor
humidity_sensor = DTH(Pin('P23', mode=Pin.OPEN_DRAIN), 0)
time.sleep(2)

# Relay for water pump
pump_relay = Pin('P20', mode=Pin.OUT)

mqtt_client = connections.adafruit_connect(keys.adafruit_user,
                                           keys.adafruit_key)

def measure_temperature() -> float:
    """Get a temperature reading from the temperature sensor"""
    temp_sensor_millivolts = temp_sensor.voltage()
    ambient_temperature = (temp_sensor_millivolts - 500) / 10.0
    return ambient_temperature


def measure_light() -> int:
    """Get a light reading from the light sensor"""
    light_millivolts = light_sensor()
    light_percentage = round((light_millivolts / 1024) * 100)
    return light_percentage


def measure_soil_moisture() -> int:
    """Get a soil moisture reading from the soil sensor"""
    moisture_sensor_power.value(1)
    time.sleep(2)
    soil_moisture_sensor_volts = soil_moisture_sensor.value()
    moisture_sensor_power.value(0)
    time.sleep(2)
    soil_moisture_percentage = round(((4095 - soil_moisture_sensor_volts) / 4095) * 100)
    return soil_moisture_percentage


def measure_humidity() -> int:
    return humidity_sensor.read()


def water_plant():
    """Activate the water pump for five seconds"""
    pump_relay.value(1)
    time.sleep(5)
    pump_relay.value(0)


def connect_wlan_adafruit():
    """Make a new connection to WLAN and Adafruit MQTT"""
    pycom.heartbeat(False)
    pycom.rgbled(0x7f7f00)
    print('No WLAN connection, attempting to reconnect...')
    connections.wlan_connect(keys.wlan_ssid, keys.wlan_pw)
    mqtt_client = connections.adafruit_connect(keys.adafruit_user,
                                               keys.adafruit_key)
    time.sleep(2)
    return mqtt_client


def reconnect_adafruit():
    """Re-establish connection to Adafruit MQTT"""
    pycom.heartbeat(False)
    pycom.rgbled(0x007f00)
    while mqtt_client.is_conn_issue():
        mqtt_client.reconnect()
    else:
        mqtt_client.resubscribe()
    time.sleep(2)


def main():
    global mqtt_client

    if not connections.wlan.isconnected():
        mqtt_client = connect_wlan_adafruit()

    if mqtt_client.is_conn_issue():
        reconnect_adafruit()

    pycom.heartbeat(True)

    mqtt_client.check_msg()
    mqtt_client.send_queue()

    try:
        # Temperature sensor
        ambient_temperature = measure_temperature()
        print('Temperature: ' + str(ambient_temperature) + 'C')

        # Light sensor
        light_percentage = measure_light()
        print('Light: ' + str(light_percentage) + '%')

        # Soil moisture sensor
        soil_moisture_percentage = measure_soil_moisture()
        print('Soil moisture: ' + str(soil_moisture_percentage) + '%')

        # Digital humidity sensor
        dht11_measurement = measure_humidity()
        if dht11_measurement.is_valid():
            humidity_percentage = dht11_measurement.humidity
            print('Humidity: ' + str(humidity_percentage) + '%')
        else:
            print('DHT11 Error code: ' + str(dht11_measurement.error_code))

        print('Publishing readings to Adafruit')
        data_message = {'Plant_sensor': {
                        'tempsensor': ambient_temperature,
                        'lightsensor': light_percentage,
                        'moisturesensor': soil_moisture_percentage,
                        'humiditysensor': humidity_percentage
                        }}

        mqtt_client.publish(topic='YOUR_ADAFRUIT_USERNAME/feeds/plant-system',
                            msg=json.dumps(data_message))

    except Exception as error:
        print('An exception occured when reading from sensors / sending data:')
        print(error)

    # Water pump
    if soil_moisture_percentage <= 10:
        water_plant()


end_setup = time.time()

print('Setup cycle time: ' + str(end_setup - start_setup))

while True:
    start_main = time.time()
    main()
    end_main = time.time()
    print('Main cycle time: ' + str(end_main - start_main))
    print('Sleeping to save power')
    sleep(1000*300, True)
    time.sleep(5)
