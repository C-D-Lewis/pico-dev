from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keycode import Keycode
import json

from modules import constants, screensavers, utils

macro_map = {}

# Map of keys on each layer to macro functionality
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
def handle(config):
  # Validate
  if not all(key in config for key in ['type', 'value', 'color']):
    raise Exception('Missing config values')

  if config['type'] == 'control_code':
    consumer_control.send(getattr(Keycode, config['value']))

  # # Write some text as a keyboard
  # if 'text' in config:
  #   layout.write(config['text'])

  # # Key combo
  # if 'combo' in config:
  #   keyboard.press(*config['combo'])
  #   keyboard.release_all()

  # # Sequence of keys or key combos
  # if 'sequence' in config:
  #   for item in config['sequence']:
  #     if isinstance(item, tuple):
  #       keyboard.press(*item)
  #     else:
  #       keyboard.press(item)
  #     time.sleep(0.2)
  #     keyboard.release_all()
  #     time.sleep(0.5)

  # # Run a custom functionn
  # if 'custom' in config:
  #   config['custom']()

  # # Search in Start menu and then press enter to launch
  # if 'search' in config:
  #   utils.start_menu_search(keyboard, layout, config['search'])