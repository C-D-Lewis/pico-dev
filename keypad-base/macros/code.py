#
# Macro pad software for Raspberry Pi Pico W running Adafruit CircuitPython.
#
# If the SCREENSAVER_CLOCK screensaver isn't used, WiFi doesn't need to be
# configured and the relevant settings.toml lines can be disabled with '#'.
#
# Latest version of these files can be found at:
#   https://github.com/C-D-Lewis/pico-dev/blob/main/keypad-base
#

import time

from modules import constants, network, macros, screensavers, utils

##################################### State ####################################

# Set up Keybow and other libraries
from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
keybow = PMK(Hardware())
keys = keybow.keys

# TODO: Shared keypad module instead of above
# import kpd
# keys = kpd.get_keys()

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

  # Home wakes the keypad up
  # If the screensaver is active, it will be deactivated and re-enabled
  if screensavers.is_active():
    if key.number == 0:
      screensavers.set_is_active(False)
      screensavers.set_disabled(False)
      utils.select_layer(keys, 0)

    return

  # Layer select - sleep, up, down
  if key.number == 0:
    screensavers.start(keys)
    return
  if key.number == 4 and current_layer > 0:
    utils.select_layer(keys, current_layer - 1)
    return
  if key.number == 8 and current_layer < (macros.get_num_layers() - 1):
    utils.select_layer(keys, current_layer + 1)
    return
  # Unhandled nav keys
  if key.number in constants.NAV_KEYS:
    return

  # Attempt to run the macro
  try:
    config = macros.get_macro_map()[current_layer][key.number]

    macros.handle(config, keys)
  except Exception:
    # Failed to send or some other error, don't crash
    key.set_led(*constants.COLOR_RED)
    time.sleep(0.5)

##################################### Main #####################################

#
# Animation played on startup with integrated steps
#
def boot_sequence():
  keys[0].set_led(*constants.COLOR_LIGHT_GREY)
  network.connect_wifi(keys)
  time.sleep(0.25)
  keys[0].set_led(*constants.COLOR_GREY)

  keys[4].set_led(*constants.COLOR_LIGHT_GREY)
  network.update_time(keys)
  time.sleep(0.25)
  keys[4].set_led(*constants.COLOR_GREY)

  keys[8].set_led(*constants.COLOR_LIGHT_GREY)
  macros.load(keys)
  time.sleep(0.25)
  keys[8].set_led(*constants.COLOR_GREY)

  keys[12].set_led(*constants.COLOR_LIGHT_GREY)
  time.sleep(0.25)
  keys[12].set_led(*constants.COLOR_GREY)

#
# Setup keybow handlers
#
def setup_key_handlers():
  macro_map = macros.get_macro_map()

  # Attach key handlers
  for key in keys:
    @keybow.on_press(key)
    def press_handler(key):
      # Key is never used
      if (
        key.number not in macro_map[utils.get_current_layer()]
        and key.number not in constants.NAV_KEYS
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
        and key.number not in constants.NAV_KEYS
      ):
        return

      if screensavers.is_active():
        return

      # Home, layer up and down
      if key.number in constants.NAV_KEYS:
        keys[0].set_led(*utils.darken(constants.COLOR_LIGHT_GREY))
        keys[4].set_led(*(constants.COLOR_LIGHT_GREY if current_layer > 0 else constants.COLOR_OFF))
        keys[8].set_led(*(constants.COLOR_LIGHT_GREY if current_layer < (macros.get_num_layers() - 1) else constants.COLOR_OFF))
        return

      # Layer configured key, restore color
      key.set_led(*utils.parse_color(macro_map[current_layer][key.number]['color']))

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
      time.sleep(1)
      screensavers.update_screensaver(keys)

main()
