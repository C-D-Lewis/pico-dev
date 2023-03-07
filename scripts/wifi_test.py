from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
import usb_hid

keybow = PMK(Hardware())
keys = keybow.keys
keys[0].set_led(0, 0, 0)

import os
import wifi
import socketpool
import ipaddress
import ssl
import adafruit_requests

pool = None

#
# Connect to WiFi
#
def connect_wifi():
  global pool
  global session

  wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
  pool = socketpool.SocketPool(wifi.radio)
  session = adafruit_requests.Session(pool, ssl.create_default_context())
  keys[0].set_led(64, 64, 0)

connect_wifi()

res = session.get("https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fwww.tomshardware.com%2Ffeeds%2Fall")
json = res.json()
# text = res.text

keys[0].set_led(0, 64, 0)
