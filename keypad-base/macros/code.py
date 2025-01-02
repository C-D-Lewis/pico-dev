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
import time
import usb_hid

from modules import constants, network, macros, screensavers, utils

##################################### State ####################################

# Set up Keybow and other libraries
from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
keybow = PMK(Hardware())
keys = keybow.keys

# import kpd
# keys = kpd.get_keys()

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

# Program state
last_used = time.time()

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
  current_layer = utils.get_current_layer()

  # Layer select wakes the keypad up
  if key.number == 0:
    screensavers.set_is_active(False)

  if screensavers.is_active():
    return

  # Layer select - home, up, down
  if key.number == 0:
    utils.select_layer(keys, 0)
    return
  if key.number == 4 and current_layer > 0:
    utils.select_layer(keys, current_layer - 1)
    return
  if key.number == 8 and current_layer < (macros.get_num_layers() - 1):
    utils.select_layer(keys, current_layer + 1)
    return

  # Unhandled selection keys
  if key.number in constants.LAYER_SELECTION_KEYS:
    return

  # Layer configured key
  config = macros.get_macro_map(keys)[current_layer][key.number]

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

      # Home, layer up and down
      if key.number in [0, 4, 8]:  # FIXME: Elegant way to use LAYER_SELECTION_KEYS?
        keys[key.number].set_led(*constants.COLOR_UNSELECTED_LAYER)
        return
      # Unused selection keys
      if key.number in constants.LAYER_SELECTION_KEYS:
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
      screensavers.start(keys)

    if screensavers.is_active():
      screensavers.update_screensaver(keys)

main()
