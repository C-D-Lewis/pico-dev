import adafruit_ntp
import adafruit_requests
import rtc
import socketpool
import ssl
import time
import wifi

# Local modules
import constants
import config

#
# Connect to WiFi, if enabled
#
def connect_wifi(keys):
  if not config.IS_WIFI_ENABLED:
    return

  global pool
  global session

  keys[0].set_led(*constants.COLOR_YELLOW)
  time.sleep(0.2)
  wifi.radio.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
  pool = socketpool.SocketPool(wifi.radio)
  session = adafruit_requests.Session(pool, ssl.create_default_context())
  keys[0].set_led(*constants.COLOR_GREEN)

#
# Update time from NTP, if WiFi enabled
#
def update_time(keys):
  if not config.IS_WIFI_ENABLED:
    return

  keys[4].set_led(*constants.COLOR_YELLOW)
  time.sleep(0.2)

  # This gets stuck sometimes
  try:
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)
    r = rtc.RTC()
    r.datetime = ntp.datetime
    keys[4].set_led(*constants.COLOR_GREEN)
  except Exception:
    keys[4].set_led(*constants.COLOR_RED)
    time.sleep(0.5)
    update_time()
