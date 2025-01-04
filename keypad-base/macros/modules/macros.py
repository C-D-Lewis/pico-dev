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

#
# Load macros from JSON file
#
def load(keys):
  global macro_map
  
  try:
    with open(constants.MACROS_JSON_PATH, 'r', encoding='utf-8') as json_file:
      macros_json = json.load(json_file)
      
      media_layer = macros_json['media']

      numpad_layer = macros_json['numpad']

      applications_layer = macros_json['applications']

      windows_layer = macros_json['windows']

      misc_layer = macros_json['misc']

      macro_map = {
        0: media_layer,
        1: numpad_layer,
        2: applications_layer,
        3: windows_layer,
        4: misc_layer
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
  return 5
