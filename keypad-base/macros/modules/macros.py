from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
import json
import time
import usb_hid

from modules import constants, screensavers, utils

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

macro_map = {}

# Use macros.json to map keys on each layer to macro functionality
# NOTE: Keys 0, 4, 8, 12 are the layer selection keys and can't be used for macros
#
# Macros are all other keys with the following options for specifying functionality:
#
#   'control_code' - Send a special keyboard control code
#   'combo'        - Send a key combo
#   'custom'       - Run a custom Python function
#   'text'         - Enter some text as a keyboard
#   'sequence'     - Send a sequence of keys or key combos
#   'search'       - Search in Start menu and then press enter. Useful for installed apps.
#
# See macros.example.json for an example

#
# Replace JSON string keys for numbers with numbers
#
def int_keys(obj):
  new_obj = {}

  for key, value in obj.items():
    if key.isdigit():
      new_obj[int(key)] = value
    else:
      new_obj[key] = value

  return new_obj

#
# Load macros from JSON file
#
def load(keys):
  global macro_map
  
  try:
    with open(constants.MACROS_JSON_PATH, 'r') as json_file:
      macros_json = json.load(json_file)
      
      # TODO: Support new layers from macros.json
      macro_map = {
        0: int_keys(macros_json['media']),
        1: int_keys(macros_json['numpad']),
        2: int_keys(macros_json['applications']),
        3: int_keys(macros_json['windows']),
        4: int_keys(macros_json['misc'])
      }

      keys[8].set_led(*constants.COLOR_GREEN)
  except Exception:
    keys[8].set_led(*constants.COLOR_RED)
    raise Exception('Failed to load macros')

#
# Get the loaded macro map
#
def get_macro_map():
  return macro_map

#
# Number of layers to choose from.
#
def get_num_layers():
  return len(macro_map)

#
# Parse and handle a macro config when pressed, based on 'type'
#
def handle(config, keys):
  # Validate
  if not all(key in config for key in ['type', 'value', 'color']):
    raise Exception('Missing config values')

  # Send control code for media actions
  if config['type'] == 'control_code':
    consumer_control.send(getattr(ConsumerControlCode, config['value']))
    return

  # Write some text as a keyboard
  if config['type'] == 'text':
    layout.write(config['value'])
    return

  # Key combo
  if config['type'] == 'combo':
    values = [getattr(Keycode, value) for value in config['value']]
    keyboard.press(*tuple(values))
    keyboard.release_all()
    return

  # Sequence of keys or key combos
  if config['type'] == 'sequence':
    for item in config['value']:
      if isinstance(item, list):
        values = [getattr(Keycode, value) for value in item]
        keyboard.press(*tuple(values))
      else:
        keyboard.press(getattr(Keycode, item))
      time.sleep(0.2)
      keyboard.release_all()
      time.sleep(0.5)
    return

  # Run a custom function - must be runnable from this scope
  if config['type'] == 'custom':
    eval(config['value'])
    return

  # Search in Start menu and then press enter to launch
  if config['type'] == 'search':
    utils.start_menu_search(keyboard, layout, config['value'])
    return
