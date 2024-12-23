#
# Macro pad software for Raspberry Pi Pico W running Adafruit CircuitPython.
#
# If the SCREENSAVER_CLOCK screensaver isn't used, WiFi doesn't need to be
# configured and the relevant settings.toml lines can be disabled with '#'.
#
# Latest version of this file can be found at:
#   https://github.com/C-D-Lewis/pico-dev/blob/main/keypad-base
#

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

################################### Constants ##################################

# Layer selection key numbers
LAYER_SELECTION_KEYS = (0, 4, 8, 12)
# Seconds until autosleep
SLEEP_TIMEOUT_S = 60
# Clock digit LED sequence
CLOCK_LED_SEQ = [2, 3, 7, 11, 15, 14, 13, 12, 8, 4, 0, 1]
# Total number of digits
TOTAL_CLOCK_DIGITS = 12
# Keys used for D6 display
D6_AREA_KEYS = [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15]

# settings.toml configuration
# Wi-Fi SSID
WIFI_SSID = os.getenv('WIFI_SSID')
# Wi-Fi password
WIFI_PASSWORD = os.getenv('WIFI_PASSWORD')
# The current screensaver
SELECTED_SCREENSAVER = os.getenv('SCREENSAVER')
# If WiFi is not configured, don't do anything NTP or internet related
IS_WIFI_ENABLED = WIFI_SSID is not None and WIFI_PASSWORD is not None

# Colors
COLOR_OFF = (0, 0, 0)
COLOR_WHITE = (128, 128, 128)
COLOR_RED = (64, 0, 0)
COLOR_GREEN = (0, 64, 0)
COLOR_BLUE = (0, 0, 64)
COLOR_YELLOW = (64, 64, 0)
COLOR_PURPLE = (78, 0, 105)
COLOR_SELECTED_LAYER = (32, 32, 32)
COLOR_UNSELECTED_LAYER = (4, 4, 4)
COLOR_SLEEPING = (2, 2, 2)

# Other layer IDs, greater than 3
OTHER_LAYER_RAINBOW = 4

# Screensavers
SCREENSAVER_NONE = "NONE"
SCREENSAVER_CLOCK = "CLOCK"
SCREENSAVER_RAINBOW = "RAINBOW"
SCREENSAVER_STARRY_NIGHT = "STARRY_NIGHT"

################################# Configuration ################################

# Timezone offset in hours, such as BST
TZ_OFFSET_H = 1

# Map of keys on each layer to macro functionality
# NOTE: Keys 0, 4, 8, 12 are the layer selection keys and can't be used for macros
#
# The main 4 layers are 0 - 3
# Macros are all other keys with the following options for specifying functionality:
#
#   'control_code' - Send a special keyboard control code
#   'combo'        - Send a key combo
#   'custom'       - Run a custom Python function
#   'text'         - Enter some text as a keyboard
#   'sequence'     - Send a sequence of keys or key combos
#   'search'       - Search in Start menu and then press enter. Useful for installed apps.
#
MACRO_MAP = {
  # Media layer
  0: {
    1: {
      'control_code': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
      'color': COLOR_BLUE
    },
    2: {
      'control_code': ConsumerControlCode.PLAY_PAUSE,
      'color': COLOR_GREEN
    },
    3: {
      'control_code': ConsumerControlCode.SCAN_NEXT_TRACK,
      'color': COLOR_BLUE
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
    # Discord mute (must add this custom keybind to work in background)
    13: {
      'combo': (Keycode.CONTROL, Keycode.SHIFT, Keycode.M),
      'color': COLOR_RED
    }
  },
  # Applications layer
  1: {
    1: {
      'search': 'spotify',
      'color': COLOR_GREEN
    },
    2: {
      'search': 'steam',
      'color': (0, 0, 16)
    },
    3: {
      'search': 'discord',
      'color': (0, 32, 64)
    },
    5: {
      'search': 'firefox',
      'color': (25, 0, 0)
    }
  },
  # Windows layer
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
      'custom': lambda: start_screensaver()
    },
    14: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.R],
      'color': (0, 32, 0),
      'custom': lambda: start_screensaver()
    },
    15: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.U],
      'color': (32, 0, 0),
      'custom': lambda: start_screensaver()
    }
  },
  # Other (meta, web? numpad?) layer
  3: {
    1: {
      'custom': lambda: select_layer(OTHER_LAYER_RAINBOW),
      'color': COLOR_PURPLE
    },
    # 13: {
    #   'custom': lambda: roll_d6(),
    #   'color': COLOR_WHITE
    # },
    14: {
      'custom': lambda: toggle_screensaver_disabled(),
      'color': (16, 16, 16)
    },
    15: {
      'custom': lambda: start_screensaver(),
      'color': (0, 0, 16)
    }
  },
  # Layers below here are other pages, not part of the main macro pad
  # Rainbow
  4: {}
}


##################################### State ####################################

# Set up Keybow and other libraries
keybow = PMK(Hardware())
keys = keybow.keys
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

# Program state
current_layer = 0
screensaver_active = False
screensaver_disabled = False
last_used = time.time()
last_second_index = 0
sockets = None
session = None
rainbow_state = {}
starry_sky_state = {
  'key': 0,
  'val': 0,
  'dir': 1,
}

##################################### Utils ####################################

#
# Launch a program via Start menu query
#
def start_menu_search(query):
  keyboard.press(Keycode.GUI)
  keyboard.release_all()
  time.sleep(0.2)
  layout.write(query)
  time.sleep(1)
  layout.write('\n')

#
# Set some LEDs to same color
#
def set_leds(arr, color):
  for i in arr:
    keys[i].set_led(*color)

#
# Make a color darker by halving its values equally
#
def darken(color):
  return (color[0] / 2, color[1] / 2, color[2] / 2)

################################### Roll a D6 ##################################

#
# Show D6 result visually
#
def show_d6_result(result):
  for index in D6_AREA_KEYS:
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
# Roll a D6. Flash some numbers, then settle on a result
#
def roll_d6():
  rolls = 0
  result = 0

  while rolls < 20:
    new_result = random.randint(1, 6)
    while new_result == result:
      new_result = random.randint(1, 6)

    result = new_result
    show_d6_result(result)

    time.sleep(0.05 + (0.01 * rolls))
    rolls = rolls + 1

################################# Screensavers #################################

#
# Update rainbow for a given key
#
def update_rainbow(key):
  rainbow_min = 8
  rainbow_max = 128

  if key not in rainbow_state:
    dist = round((key * 4) / 4) + (key % 4)
    rainbow_state[key] = {
      'rgb': [dist * 4, dist * 8, dist * 16],
      'dirs': [1, 1, 1]
    }

  rgb = rainbow_state[key]['rgb']
  dirs = rainbow_state[key]['dirs']

  # Move and bracket
  rgb[0] += (5 * dirs[0])
  rgb[1] += (5 * dirs[1])
  rgb[2] += (5 * dirs[2])
  rgb[0] = min(max(rgb[0], rainbow_min), rainbow_max)
  rgb[1] = min(max(rgb[1], rainbow_min), rainbow_max)
  rgb[2] = min(max(rgb[2], rainbow_min), rainbow_max)

  # Change direction
  if rgb[0] >= rainbow_max or rgb[0] <= rainbow_min:
    dirs[0] *= -1
  if rgb[1] >= rainbow_max or rgb[1] <= rainbow_min:
    dirs[1] *= -1
  if rgb[2] >= rainbow_max or rgb[2] <= rainbow_min:
    dirs[2] *= -1

  keys[key].set_led(rgb[0], rgb[1], rgb[2])

#
# Get clock LED digit for based on number to divide by
#
def get_clock_digit(value, divisor):
  index = math.floor(math.floor((value * 100) / divisor) / 100 * TOTAL_CLOCK_DIGITS)
  return CLOCK_LED_SEQ[index]

#
# Draw clock animation
#
def draw_clock():
  global last_second_index

  # now is array of (year, month, mday, hour, minute, second, ...)
  now = time.localtime()
  hours = (now[3] + TZ_OFFSET_H) % 24
  hours_12h = hours - 12 if hours >= 12 else hours
  minutes = now[4]
  seconds = now[5]

  # Positions of hands around the face
  hours_index = get_clock_digit(hours_12h, 12)
  minutes_index = get_clock_digit(minutes, 60)
  seconds_index = get_clock_digit(seconds, 60)

  # Prevent flickering by updating only for each new seconds hand position
  if seconds_index != last_second_index:
    last_second_index = seconds_index
    for key in keys:
      key.set_led(*COLOR_OFF)

  # Hands
  keys[hours_index].set_led(*darken(COLOR_RED))
  keys[minutes_index].set_led(*darken(COLOR_BLUE))
  keys[seconds_index].set_led(*darken(COLOR_YELLOW))

#
# Update starry sky screensaver
#
def update_starry_night():
  # Update brightness
  starry_sky_state['val'] += starry_sky_state['dir']
  val = starry_sky_state['val']
  keys[starry_sky_state['key']].set_led(val, val, val * 3)

  # Pick new key when dark
  if starry_sky_state['val'] <= 0:
    last_key = starry_sky_state['key']
    next_key = last_key
    while next_key == last_key:
      next_key = random.randint(0, 15)
    
    starry_sky_state['key'] = next_key
    starry_sky_state['dir'] = 1
    starry_sky_state['val'] = 1
    keys[last_key].set_led(*COLOR_OFF)
  
  # When bright, reverse direction
  elif starry_sky_state['val'] >= 64:
    starry_sky_state['dir'] = -1

#
# Show clock animation if WiFI, else just the wake button
#
def update_screensaver():
  now = time.localtime()
  hours_24h = (now[3] + TZ_OFFSET_H) % 24

  # No dazzling screensavers between 11 PM ana 9 AM
  if hours_24h >= 23 or hours_24h <= 9:
    pass
  elif SELECTED_SCREENSAVER == SCREENSAVER_NONE:
    pass
  elif SELECTED_SCREENSAVER == SCREENSAVER_CLOCK and IS_WIFI_ENABLED:
    draw_clock()
  elif SELECTED_SCREENSAVER == SCREENSAVER_RAINBOW:
    for key in keys:
      update_rainbow(key.number)
  elif SELECTED_SCREENSAVER == SCREENSAVER_STARRY_NIGHT:
    update_starry_night()
  
  # Always show wakeup key
  keys[0].set_led(*COLOR_SLEEPING)

#
# Go to sleep state and show screensaver
#
def start_screensaver():
  global screensaver_active
  screensaver_active = True

  select_layer(0)

  for key in keys:
    key.set_led(*COLOR_OFF)
  keys[0].set_led(*COLOR_SLEEPING)

#
# Toggle stay awake mode
#
def toggle_screensaver_disabled():
  global screensaver_disabled
  screensaver_disabled = not screensaver_disabled

  if screensaver_disabled:
    select_layer(0)
  else:
    start_screensaver()

############################### Layers and macros ##############################

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
# Select a layer and update keypad with its colors
#
def select_layer(index):
  global current_layer
  current_layer = index

  # Some other layer
  if index > 3:
    return

  # A macro page
  for key in keys:
    key.set_led(*COLOR_OFF)

    # Update layer indicator
    if key.number in LAYER_SELECTION_KEYS:
      key.set_led(*COLOR_SELECTED_LAYER if key.number / 4 == current_layer else COLOR_UNSELECTED_LAYER)

    # Not configured
    if key.number not in MACRO_MAP[current_layer]:
      continue

    key.set_led(*MACRO_MAP[current_layer][key.number]['color'])

#
# Handle a key press event
#
def handle_key_press(key):
  global screensaver_active
  global last_used

  last_used = time.time()

  # Layer select wakes the keypad up
  if key.number == 0:
    screensaver_active = False

  if screensaver_active:
    return

  # Layer select
  if key.number in LAYER_SELECTION_KEYS:
    select_layer(key.number / 4)
    key.set_led(*COLOR_SELECTED_LAYER)
    return

  # Layer configured key
  config = MACRO_MAP[current_layer][key.number]

  try:
    # Issues some keyboard control code
    if 'control_code' in config:
      consumer_control.send(config['control_code'])
    
    # Write some text as a keyboard
    if 'text' in config:
      layout.write(config['text'])
    
    # Key combo
    if 'combo' in config:
      keyboard.press(*config['combo'])
      keyboard.release_all()

    # Sequence of keys or key combos
    if 'sequence' in config:
      for item in config['sequence']:
        if isinstance(item, tuple):
          keyboard.press(*item)
        else:
          keyboard.press(item)
        time.sleep(0.2)
        keyboard.release_all()
        time.sleep(0.5)

    # Run a custom functionn
    if 'custom' in config:
      config['custom']()

    # Search in Start menu and then press enter to launch
    if 'search' in config:
      start_menu_search(config['search'])
  except Exception:
    # Failed to send or some other error, don't crash
    key.set_led(*COLOR_RED)
    time.sleep(0.5)

#################################### Network ###################################

#
# Connect to WiFi, if enabled
#
def connect_wifi():
  if not IS_WIFI_ENABLED:
    keys[0].set_led(*COLOR_YELLOW)
    time.sleep(0.2)
    keys[0].set_led(*COLOR_OFF)
    return

  global pool
  global session

  keys[0].set_led(*COLOR_YELLOW)
  time.sleep(0.2)
  wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
  pool = socketpool.SocketPool(wifi.radio)
  session = adafruit_requests.Session(pool, ssl.create_default_context())
  keys[0].set_led(*COLOR_GREEN)

#
# Update time from NTP, if WiFi enabled
#
def update_time():
  if not IS_WIFI_ENABLED:
    keys[4].set_led(*COLOR_YELLOW)
    time.sleep(0.2)
    keys[4].set_led(*COLOR_OFF)
    return

  keys[4].set_led(*COLOR_YELLOW)
  time.sleep(0.2)

  # This gets stuck sometimes
  try:
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)
    r = rtc.RTC()
    r.datetime = ntp.datetime
    keys[4].set_led(*COLOR_GREEN)
  except Exception:
    keys[4].set_led(*COLOR_RED)
    time.sleep(0.5)
    update_time()

##################################### Main #####################################

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

#
# Handle updates when layer is not a macro layer
#
def update_other_layer():
  # Rainbow
  if current_layer == OTHER_LAYER_RAINBOW:
    for key in keys:
      update_rainbow(key.number)
  
  # Other misc layer updates here

#
# Setup keybow handlers
#
def setup_key_handlers():
  # Attach key handlers
  for key in keys:
    @keybow.on_press(key)
    def press_handler(key):
      # Key is never used
      if (
        key.number not in MACRO_MAP[current_layer] 
        and key.number not in LAYER_SELECTION_KEYS
      ):
        return

      handle_key_press(key)
      if not screensaver_active:
        flash_confirm(key)

    @keybow.on_release(key)
    def release_handler(key):
      # Key is never used
      if (
        key.number not in MACRO_MAP[current_layer]
        and key.number not in LAYER_SELECTION_KEYS
      ):
        return

      if screensaver_active:
        return

      # Selected layer, restore color
      if key.number in LAYER_SELECTION_KEYS:
        key.set_led(*COLOR_SELECTED_LAYER if key.number / 4 == current_layer else COLOR_UNSELECTED_LAYER)
        return

      # Layer configured key, restore color
      key.set_led(*MACRO_MAP[current_layer][key.number]['color'])

#
# The main function
#
def main():
  global last_used

  boot_sequence()
  time.sleep(0.5)
  last_used = time.time()

  setup_key_handlers()
  select_layer(0)

  while True:
    keybow.update()

    update_other_layer()

    # Time out and go to sleep if nothing is pressed for a while and won't stay awake
    now = time.time()
    if (
      now - last_used > SLEEP_TIMEOUT_S
      and not screensaver_disabled
      and not screensaver_active
      and now > SLEEP_TIMEOUT_S
    ):
      start_screensaver()

    if screensaver_active:
      update_screensaver()

main()
