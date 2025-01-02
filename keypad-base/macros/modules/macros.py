from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keycode import Keycode

from modules import constants, screensavers, utils

#
# IF YOU CUSTOMIZE YOUR MACROS, REMEMBER TO REPLACE THEM AFTER UPDATING THIS FILE
#

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
def get_macro_map(keys):
  media_layer = {
    1: {
      'control_code': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
      'color': constants.COLOR_BLUE
    },
    2: {
      'control_code': ConsumerControlCode.PLAY_PAUSE,
      'color': constants.COLOR_GREEN
    },
    3: {
      'control_code': ConsumerControlCode.SCAN_NEXT_TRACK,
      'color': constants.COLOR_BLUE
    },
    5: {
      'control_code': ConsumerControlCode.VOLUME_DECREMENT,
      'color': constants.COLOR_YELLOW
    },
    6: {
      'control_code': ConsumerControlCode.MUTE,
      'color': constants.COLOR_RED
    },
    7: {
      'control_code': ConsumerControlCode.VOLUME_INCREMENT,
      'color': constants.COLOR_YELLOW
    },
    # Discord mute (must add this custom keybind to work in background)
    13: {
      'combo': (Keycode.CONTROL, Keycode.SHIFT, Keycode.M),
      'color': constants.COLOR_RED
    }
  }

  numpad_layer = {
    1: {
      'text': '7',
      'color': constants.COLOR_UNSELECTED_LAYER
    },
    2: {
      'text': '8',
      'color': constants.COLOR_SELECTED_LAYER
    },
    3: {
      'text': '9',
      'color': constants.COLOR_UNSELECTED_LAYER
    },
    5: {
      'text': '4',
      'color': constants.COLOR_SELECTED_LAYER
    },
    6: {
      'text': '5',
      'color': constants.COLOR_WHITE
    },
    7: {
      'text': '6',
      'color': constants.COLOR_SELECTED_LAYER
    },
    9: {
      'text': '1',
      'color': constants.COLOR_UNSELECTED_LAYER
    },
    10: {
      'text': '2',
      'color': constants.COLOR_SELECTED_LAYER
    },
    11: {
      'text': '3',
      'color': constants.COLOR_UNSELECTED_LAYER
    }
  }

  applications_layer = {
    1: {
      'search': 'spotify',
      'color': constants.COLOR_GREEN
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
  }

  windows_layer = {
    1: {
      'combo': (Keycode.CONTROL, Keycode.SHIFT, Keycode.ESCAPE),
      'color': (0, 32, 0)
    },
    2: {
      'combo': (Keycode.GUI, Keycode.E),
      'color': constants.COLOR_YELLOW
    },
    13: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.S],
      'color': (0, 0, 32)
    },
    14: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.R],
      'color': (0, 32, 0)
    },
    15: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.U],
      'color': (32, 0, 0)
    }
  }

  misc_layer = {
    14: {
      'custom': lambda: screensavers.toggle_screensaver_disabled(keys),
      'color': (16, 16, 16)
    },
    15: {
      'custom': lambda: screensavers.start_screensaver(keys),
      'color': (0, 0, 16)
    }
  }

  return {
    0: media_layer,
    1: numpad_layer,
    2: applications_layer,
    3: windows_layer,
    4: misc_layer
  }

#
# Number of layers to choose from.
#
def get_num_layers():
  return 5
