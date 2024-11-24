from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
import adafruit_ntp
import adafruit_requests
import ipaddress
import math
import os
import rtc
import socketpool
import ssl
import time
import usb_hid
import wifi
import random

# Index selection key numbers
INDEX_SELECTION_KEYS = (0, 4, 8, 12)
# Seconds until autosleep
SLEEP_TIMEOUT_S = 60
# Clock digit LED sequence
DIGIT_LED_SEQ = [2, 3, 7, 11, 15, 14, 13, 12, 8, 4, 0, 1]
# Total number of digits
TOTAL_DIGITS = 12
# Keys used for D6 display
FUNCTION_AREA_KEYS = [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15]

# Off color
COLOR_OFF = (0, 0, 0)
# Flash color
COLOR_WHITE = (128, 128, 128)
# Mid red color
COLOR_RED = (64, 0, 0)
# Mid green color
COLOR_GREEN = (0, 64, 0)
# Mid blue color
COLOR_BLUE = (0, 0, 64)
# Mid yellow color
COLOR_YELLOW = (64, 64, 0)
# White when selected layer
COLOR_SELECTED_LAYER = (32, 32, 32)
# White for unselected layer
COLOR_UNSELECTED_LAYER = (4, 4, 4)
# When sleeping
COLOR_SLEEPING = (2, 2, 2)

# Timezone offset in hours, such as BST
TZ_OFFSET_H = 1

# Map of keys on each layer
KEY_MAP = {
  # Media/utilty
  0: {
    1: {
      'control_code': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
      'color': (0, 0, 64)
    },
    2: {
      'control_code': ConsumerControlCode.PLAY_PAUSE,
      'color': COLOR_GREEN
    },
    3: {
      'control_code': ConsumerControlCode.SCAN_NEXT_TRACK,
      'color': (0, 0, 64)
    },
    5: {
      'control_code': ConsumerControlCode.VOLUME_DECREMENT,
      'color': COLOR_YELLOW
    },
    6: {
      'control_code': ConsumerControlCode.MUTE,
      'color': COLOR_RED
    },
    7: {
      'control_code': ConsumerControlCode.VOLUME_INCREMENT,
      'color': COLOR_YELLOW
    },
    # Mute Discord mic
    13: {
      'combo': (Keycode.CONTROL, Keycode.M),
      'color': COLOR_RED
    },
    15: {
      'custom': lambda: roll_d6(),
      'color': COLOR_WHITE
    }
  },
  # Applications
  1: {
    1: {
      'custom': lambda: run_program('spotify'),
      'color': COLOR_GREEN
    },
    2: {
      'custom': lambda: run_program('steam'),
      'color': (0, 0, 16)
    },
    3: {
      'custom': lambda: run_program('discord'),
      'color': (0, 32, 64)
    }
  },
  # System
  2: {
    1: {
      'combo': (Keycode.CONTROL, Keycode.SHIFT, Keycode.ESCAPE),
      'color': (0, 32, 0)
    },
    2: {
      'combo': (Keycode.GUI, Keycode.E),
      'color': COLOR_YELLOW
    },
    13: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.S],
      'color': (0, 0, 32),
      'custom': lambda: go_to_sleep()
    },
    14: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.R],
      'color': (0, 32, 0),
      'custom': lambda: go_to_sleep()
    },
    15: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.U],
      'color': (32, 0, 0),
      'custom': lambda: go_to_sleep()
    }
  },
  # Utility (web? numpad?)
  3: {
    14: {
      'custom': lambda: toggle_stay_awake(),
      'color': (16, 16, 16)
    },
    15: {
      'custom': lambda: go_to_sleep(),
      'color': (0, 0, 16)
    }
  }
}

# Set up Keybow
keybow = PMK(Hardware())
keys = keybow.keys
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

current_layer = 0
is_sleeping = False
stay_awake = False
last_used = time.time()
last_second_index = 0
sockets = None
session = None

#
# Set some LEDs to same color
#
def set_leds(arr, color):
  for i in arr:
    keys[i].set_led(*color)

#
# Show D6 result visually
#
def show_d6_result(result):
  for index in FUNCTION_AREA_KEYS:
    keys[index].set_led(*COLOR_OFF)

  if result == 1:
    set_leds([6], COLOR_WHITE)
  elif result == 2:
    set_leds([2, 10], COLOR_WHITE)
  elif result == 3:
    set_leds([9, 6, 3], COLOR_WHITE)
  elif result == 4:
    set_leds([1, 3, 9, 11], COLOR_WHITE)
  elif result == 5:
    set_leds([1, 3, 9, 11, 6], COLOR_WHITE)
  elif result == 6:
    set_leds([1, 3, 5, 7, 9, 11], COLOR_WHITE)

#
# Roll a D6. Flash some numbers, then settle
#
def roll_d6():
  count = 0
  result = 0
  while count < 20:
    next_result = random.randint(1, 6)
    while next_result == result:
      next_result = random.randint(1, 6)

    result = next_result
    show_d6_result(result)

    time.sleep(0.05 + (0.01 * count))
    count = count + 1

#
# Launch a program via Start menu query
#
def run_program(query):
  keyboard.press(Keycode.GUI)
  keyboard.release_all()
  time.sleep(0.2)
  layout.write(query)
  time.sleep(1)
  layout.write('\n')

#
# Go to dark sleep state
#
def go_to_sleep():
  global is_sleeping
  is_sleeping = True

  for key in keys:
    key.set_led(*COLOR_OFF)
  keys[0].set_led(*COLOR_SLEEPING)

#
# Toggle stay awake mode
#
def toggle_stay_awake():
  global stay_awake
  stay_awake = not stay_awake

  # Reset to layer 0 (long lived media controls)
  if stay_awake:
    set_layer(0)

#
# Flash a key to confirm an action.
#
def flash_confirm(key):
  key.set_led(*COLOR_WHITE)
  time.sleep(0.03)
  key.set_led(*COLOR_OFF)
  time.sleep(0.03)
  key.set_led(*COLOR_WHITE)
  time.sleep(0.03)
  key.set_led(*COLOR_OFF)

#
# Attach handler functions to all of the keys for this layer.
#
def set_layer(new_layer):
  global current_layer
  current_layer = new_layer

  # Update colors
  for key in keys:
    key.set_led(*COLOR_OFF)

    # Update layer indicator
    if key.number in INDEX_SELECTION_KEYS:
      key.set_led(*COLOR_SELECTED_LAYER if key.number / 4 == current_layer else COLOR_UNSELECTED_LAYER)

    # Not configured
    if key.number not in KEY_MAP[current_layer]:
      continue

    key.set_led(*KEY_MAP[current_layer][key.number]['color'])

#
# Handle a key press event
#
def handle_key_press(key):
  global is_sleeping
  global last_used

  last_used = time.time()

  # Layer select wakes
  if key.number == 0:
    is_sleeping = False

  if is_sleeping:
    return

  # Layer select
  if key.number in INDEX_SELECTION_KEYS:
    set_layer(key.number / 4)
    key.set_led(*COLOR_SELECTED_LAYER)
    return

  # Layer configured key
  config = KEY_MAP[current_layer][key.number]

  if 'control_code' in config:
    consumer_control.send(config['control_code'])
  
  if 'text' in config:
    layout.write(config['text'])
  
  if 'combo' in config:
    keyboard.press(*config['combo'])
    keyboard.release_all()

  if 'sequence' in config:
    for item in config['sequence']:
      if isinstance(item, tuple):
        keyboard.press(*item)
      else:
        keyboard.press(item)
      time.sleep(0.2)
      keyboard.release_all()
      time.sleep(0.5)

  if 'custom' in config:
    config['custom']()

#
# Make a color darker
#
def darker(color):
  return (color[0] / 2, color[1] / 2, color[2] / 2)

#
# Get clock LED digit for hours
#
def get_hour_digit(hours):
  index = math.floor(math.floor((hours * 100) / 12) / 100 * TOTAL_DIGITS)
  return DIGIT_LED_SEQ[index]

#
# Get clock LED digit for minutes
#
def get_minute_seconds_digit(minutes):
  index = math.floor(math.floor((minutes * 100) / 60) / 100 * TOTAL_DIGITS)
  return DIGIT_LED_SEQ[index]

#
# Show clock animation
#
def show_clock():
  if not wifi_enabled():
    # Key to wake
    keys[0].set_led(*COLOR_SLEEPING)
    return

  global last_second_index

  # (year, month, mday, hour, minute, second, ...)
  now = time.localtime()
  hours = (now[3] + TZ_OFFSET_H) % 24
  hours_24h = hours
  hours_12h = hours - 12 if hours >= 12 else hours
  minutes = now[4]
  seconds = now[5]

  # Indices around the face
  hours_index = get_hour_digit(hours_12h)
  minutes_index = get_minute_seconds_digit(minutes)
  seconds_index = get_minute_seconds_digit(seconds)

  # Prevent flickering
  if seconds_index != last_second_index:
    last_second_index = seconds_index
    for key in keys:
      key.set_led(*COLOR_OFF)

  # Key to wake
  keys[0].set_led(*COLOR_SLEEPING)

  # Don't dazzle at night
  if hours_24h >= 9 and hours_24h <= 23:
    # Hands
    keys[hours_index].set_led(*darker(COLOR_RED))
    keys[minutes_index].set_led(*darker(COLOR_BLUE))
    keys[seconds_index].set_led(*darker(COLOR_YELLOW))

#
# Use WiFi features only if credentials are present
#
def wifi_enabled():
  return os.getenv('WIFI_SSID') is not None and os.getenv('WIFI_PASSWORD') is not None

#
# Connect to WiFi, if enabled
#
def connect_wifi():
  if not wifi_enabled():
    keys[0].set_led(*COLOR_RED)
    time.sleep(0.3)
    keys[0].set_led(*COLOR_OFF)
    return

  global pool
  global session

  keys[0].set_led(*COLOR_YELLOW)
  time.sleep(0.2)
  wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
  pool = socketpool.SocketPool(wifi.radio)
  session = adafruit_requests.Session(pool, ssl.create_default_context())
  keys[0].set_led(*COLOR_GREEN)

#
# Update time from NTP, if WiFi enabled
#
def update_time():
  if not wifi_enabled():
    keys[4].set_led(*COLOR_RED)
    time.sleep(0.3)
    keys[4].set_led(*COLOR_OFF)
    return

  keys[4].set_led(*COLOR_YELLOW)
  time.sleep(0.2)
  ntp = adafruit_ntp.NTP(pool, tz_offset=0)
  r = rtc.RTC()
  r.datetime = ntp.datetime
  # os.environ['TZ'] = 'Europe/London'
  # time.tzset()
  keys[4].set_led(*COLOR_GREEN)

#
# Animation played on startup with integrated steps
#
def boot_sequence():
  connect_wifi()
  time.sleep(0.25)
  keys[0].set_led(*COLOR_UNSELECTED_LAYER)
  update_time()
  time.sleep(0.25)
  keys[4].set_led(*COLOR_UNSELECTED_LAYER)
  keys[8].set_led(*COLOR_SELECTED_LAYER)
  time.sleep(0.25)
  keys[8].set_led(*COLOR_UNSELECTED_LAYER)
  keys[12].set_led(*COLOR_SELECTED_LAYER)
  time.sleep(0.25)
  keys[12].set_led(*COLOR_UNSELECTED_LAYER)
  time.sleep(0.25)

# Attach handlers
for key in keys:
  @keybow.on_press(key)
  def press_handler(key):
    if key.number not in KEY_MAP[current_layer] and key.number not in INDEX_SELECTION_KEYS:
      return

    handle_key_press(key)
    flash_confirm(key)

  @keybow.on_release(key)
  def release_handler(key):
    if is_sleeping:
      return

    if key.number not in KEY_MAP[current_layer] and key.number not in INDEX_SELECTION_KEYS:
      return

    if key.number in INDEX_SELECTION_KEYS:
      key.set_led(*COLOR_SELECTED_LAYER if key.number / 4 == current_layer else COLOR_UNSELECTED_LAYER)
      return

    # Layer configured key
    key.set_led(*KEY_MAP[current_layer][key.number]['color'])

#
# The main function
#
def main():
  boot_sequence()
  time.sleep(0.5)

  # Default layer
  set_layer(0)

  # Wait for button presses
  while True:
    keybow.update()

    # Time out
    now = time.time()
    if now - last_used > SLEEP_TIMEOUT_S and not stay_awake and not is_sleeping and now > SLEEP_TIMEOUT_S:
      go_to_sleep()

    if is_sleeping:
      show_clock()

main()
