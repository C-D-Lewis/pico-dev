from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import time
import math
import usb_hid
import os
import wifi
import socketpool
import ipaddress
import ssl
import adafruit_requests

# Index selection key numbers
INDEX_SELECTION_KEYS = (0, 4, 8, 12)
# Seconds until autosleep
SLEEP_TIMEOUT_S = 60
# Clock digit LED sequence
DIGIT_LED_SEQ = [2, 3, 7, 11, 15, 14, 13, 12, 8, 4, 0, 1]

# Off color
COLOR_OFF = (0, 0, 0)
# Flash color
COLOR_FLASH = (128, 128, 128)
# White when selected layer
COLOR_SELECTED_LAYER = (32, 32, 32)
# White for unselected layer
COLOR_UNSELECTED_LAYER = (4, 4, 4)
# When sleeping
COLOR_SLEEPING = (1, 1, 1)

# Map of keys on each layer
KEY_MAP = {
  # Media
  0: {
    1: {
      'control_code': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
      'color': (0, 0, 64)
    },
    2: {
      'control_code': ConsumerControlCode.PLAY_PAUSE,
      'color': (0, 64, 0)
    },
    3: {
      'control_code': ConsumerControlCode.SCAN_NEXT_TRACK,
      'color': (0, 0, 64)
    },
    5: {
      'control_code': ConsumerControlCode.VOLUME_DECREMENT,
      'color': (64, 64, 0)
    },
    6: {
      'control_code': ConsumerControlCode.MUTE,
      'color': (64, 0, 0)
    },
    7: {
      'control_code': ConsumerControlCode.VOLUME_INCREMENT,
      'color': (64, 64, 0)
    },
    # Mute Discord mic
    13: {
      'combo': (Keycode.CONTROL, Keycode.M),
      'color': (64, 0, 0)
    }
  },
  # Applications
  1: {
    1: {
      'custom': lambda: run_program('spotify'),
      'color': (0, 64, 0)
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
      'color': (64, 64, 0)
    },
    13: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.S],
      'color': (0, 0, 32),
      'custom': lambda: go_to_sleep()
    },
    14: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.R],
      'color': (0, 32, 0)
    },
    15: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.U],
      'color': (32, 0, 0),
      'custom': lambda: go_to_sleep()
    }
  },
  # Onboard?
  3: {
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
last_used = time.time()
last_second_index = 0
sockets = None
session = None

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
  keys[0].set_led(2, 2, 2)

#
# Flash a key to confirm an action.
#
def flash_confirm(key):
  key.set_led(*COLOR_FLASH)
  time.sleep(0.03)
  key.set_led(*COLOR_OFF)
  time.sleep(0.03)
  key.set_led(*COLOR_FLASH)
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

  if 'custom' in config:
    config['custom']()

#
# Pulse while asleep
#
def sleep_pulse():
  keys[0].set_led(2, 2, 2)
  time.sleep(1)
  keybow.update()
  keys[0].set_led(*COLOR_OFF)
  time.sleep(1)

#
# Get clock LED digit for hours
#
def get_hour_digit(hours):
  index = math.floor(math.floor((hours * 100) / 12) / 100 * len(DIGIT_LED_SEQ))
  return DIGIT_LED_SEQ[index]

#
# Get clock LED digit for minutes
#
def get_minute_seconds_digit(minutes):
  index = math.floor(math.floor((minutes * 100) / 60) / 100 * len(DIGIT_LED_SEQ))
  return DIGIT_LED_SEQ[index]

#
# Show clock animation
#
def show_clock():
  global last_second_index

  # (year, month, mday, hour, minute, second, ...)
  now = time.localtime()
  hours = now[3] - 12 if now[3] > 12 else now[3]
  minutes = now[4]
  seconds = now[5]

  hours_index = get_hour_digit(hours)
  minutes_index = get_minute_seconds_digit(minutes)
  seconds_index = get_minute_seconds_digit(seconds)

  # Prevent flickering
  if seconds_index != last_second_index:
    last_second_index = seconds_index
    for key in keys:
      key.set_led(*COLOR_OFF)

  keys[hours_index].set_led(32, 0, 0)
  keys[minutes_index].set_led(0, 0, 32)
  keys[seconds_index].set_led(32, 32, 0)


#
# Animation played on startup
#
def boot_animation():
  keys[0].set_led(*COLOR_SELECTED_LAYER)
  time.sleep(0.2)
  keys[0].set_led(*COLOR_UNSELECTED_LAYER)
  keys[4].set_led(*COLOR_SELECTED_LAYER)
  time.sleep(0.2)
  keys[4].set_led(*COLOR_UNSELECTED_LAYER)
  keys[8].set_led(*COLOR_SELECTED_LAYER)
  time.sleep(0.2)
  keys[8].set_led(*COLOR_UNSELECTED_LAYER)
  keys[12].set_led(*COLOR_SELECTED_LAYER)
  time.sleep(0.2)
  keys[12].set_led(*COLOR_UNSELECTED_LAYER)
  time.sleep(0.2)

#
# Connect to WiFi
#
def connect_wifi():
  global pool
  global session

  wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
  pool = socketpool.SocketPool(wifi.radio)
  session = adafruit_requests.Session(pool, ssl.create_default_context())

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
  boot_animation()

  # Default layer
  set_layer(0)

  # Wait for button presses
  while True:
    keybow.update()

    # Time out
    now = time.time()
    if now - last_used > SLEEP_TIMEOUT_S and not is_sleeping:
      go_to_sleep()

    # if is_sleeping:
    #   time.sleep(1)

      # sleep_pulse()
      # show_clock()  # TODO: Once NTP available on WiFi

main()
