#
# Macro pad software for Raspberry Pi Pico W running Adafruit CircuitPython.
#
# If the SCREENSAVER_CLOCK screensaver isn't used, WiFi doesn't need to be
# configured and the relevant settings.toml lines can be disabled with '#'.
#
# Latest version of these files can be found at:
#   https://github.com/C-D-Lewis/pico-dev/blob/main/keypad-base
#

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
import math
import time
import usb_hid
import random

# Local modules
import constants
import config
import macros
import network
import screensavers
import utils

##################################### State ####################################

# Set up Keybow and other libraries
keybow = PMK(Hardware())
keys = keybow.keys
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

# Program state
last_used = time.time()
last_second_index = 0
sockets = None
rainbow_state = {}
starry_sky_state = {
  'key': 0,
  'val': 0,
  'dir': 1,
}

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
  index = math.floor(math.floor((value * 100) / divisor) / 100 * constants.TOTAL_CLOCK_DIGITS)
  return constants.CLOCK_LED_SEQ[index]

#
# Draw clock animation
#
def draw_clock():
  global last_second_index

  # now is array of (year, month, mday, hour, minute, second, ...)
  now = time.localtime()
  hours = (now[3] + config.TZ_OFFSET_H) % 24
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
      key.set_led(*constants.COLOR_OFF)

  # Hands
  keys[hours_index].set_led(*utils.darken(constants.COLOR_RED))
  keys[minutes_index].set_led(*utils.darken(constants.COLOR_BLUE))
  keys[seconds_index].set_led(*utils.darken(constants.COLOR_YELLOW))

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
    keys[last_key].set_led(*constants.COLOR_OFF)

  # When bright, reverse direction
  elif starry_sky_state['val'] >= 64:
    starry_sky_state['dir'] = -1

#
# Show clock animation if WiFI, else just the wake button
#
def update_screensaver():
  now = time.localtime()
  hours_24h = (now[3] + config.TZ_OFFSET_H) % 24

  # No dazzling screensavers between 11 PM ana 9 AM
  if hours_24h >= 23 or hours_24h <= 9:
    pass
  elif config.SCREENSAVER == constants.SCREENSAVER_NONE:
    pass
  elif config.SCREENSAVER == constants.SCREENSAVER_CLOCK and config.IS_WIFI_ENABLED:
    draw_clock()
  elif config.SCREENSAVER == constants.SCREENSAVER_RAINBOW:
    for key in keys:
      update_rainbow(key.number)
  if config.SCREENSAVER == constants.SCREENSAVER_STARRY_NIGHT:
    update_starry_night()

############################### Layers and macros ##############################

#
# Flash a key to confirm an action.
#
def flash_confirm(key):
  key.set_led(*constants.COLOR_WHITE)
  time.sleep(0.03)
  key.set_led(*constants.COLOR_OFF)
  time.sleep(0.03)
  key.set_led(*constants.COLOR_WHITE)
  time.sleep(0.03)
  key.set_led(*constants.COLOR_OFF)

#
# Handle a key press event
#
def handle_key_press(key):
  global last_used

  last_used = time.time()

  # Layer select wakes the keypad up
  if key.number == 0:
    screensavers.set_is_active(False)

  if screensavers.is_active():
    return

  # Layer select
  if key.number in constants.LAYER_SELECTION_KEYS:
    utils.select_layer(keys, key.number / 4)
    key.set_led(*constants.COLOR_SELECTED_LAYER)
    return

  # Layer configured key
  config = macros.get_macro_map(keys)[utils.get_current_layer()][key.number]

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
      utils.start_menu_search(keyboard, layout, config['search'])
  except Exception:
    # Failed to send or some other error, don't crash
    key.set_led(*constants.COLOR_RED)
    time.sleep(0.5)

##################################### Main #####################################

#
# Animation played on startup with integrated steps
#
def boot_sequence():
  keys[0].set_led(*constants.COLOR_SELECTED_LAYER)
  network.connect_wifi(keys)
  time.sleep(0.25)
  keys[0].set_led(*constants.COLOR_UNSELECTED_LAYER)

  keys[4].set_led(*constants.COLOR_SELECTED_LAYER)
  network.update_time(keys)
  time.sleep(0.25)
  keys[4].set_led(*constants.COLOR_UNSELECTED_LAYER)

  keys[8].set_led(*constants.COLOR_SELECTED_LAYER)
  time.sleep(0.25)
  keys[8].set_led(*constants.COLOR_UNSELECTED_LAYER)

  keys[12].set_led(*constants.COLOR_SELECTED_LAYER)
  time.sleep(0.25)
  keys[12].set_led(*constants.COLOR_UNSELECTED_LAYER)

#
# Setup keybow handlers
#
def setup_key_handlers():
  macro_map = macros.get_macro_map(keys)

  # Attach key handlers
  for key in keys:
    @keybow.on_press(key)
    def press_handler(key):
      current_layer = utils.get_current_layer()

      # Key is never used
      if (
        key.number not in macro_map[current_layer]
        and key.number not in constants.LAYER_SELECTION_KEYS
      ):
        return

      handle_key_press(key)
      if not screensavers.is_active():
        flash_confirm(key)

    @keybow.on_release(key)
    def release_handler(key):
      current_layer = utils.get_current_layer()

      # Key is never used
      if (
        key.number not in macro_map[current_layer]
        and key.number not in constants.LAYER_SELECTION_KEYS
      ):
        return

      if screensavers.is_active():
        return

      # Selected layer, restore color
      if key.number in constants.LAYER_SELECTION_KEYS:
        key.set_led(*constants.COLOR_SELECTED_LAYER if key.number / 4 == current_layer else constants.COLOR_UNSELECTED_LAYER)
        return

      # Layer configured key, restore color
      key.set_led(*macro_map[current_layer][key.number]['color'])

#
# The main function
#
def main():
  global last_used

  boot_sequence()
  time.sleep(0.5)
  last_used = time.time()

  setup_key_handlers()
  utils.select_layer(keys, 0)

  while True:
    keybow.update()

    # Time out and go to sleep if nothing is pressed for a while and won't stay awake
    now = time.time()
    if (
      now - last_used > constants.SLEEP_TIMEOUT_S
      and not screensavers.is_disabled()
      and not screensavers.is_active()
      and now > constants.SLEEP_TIMEOUT_S
    ):
      screensavers.start_screensaver(keys)

    if screensavers.is_active():
      update_screensaver()

main()
