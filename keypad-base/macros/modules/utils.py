from adafruit_hid.keycode import Keycode
import time

from modules import constants, macros

current_layer = 0

#
# Launch a program via Start menu query
#
def start_menu_search(keyboard, layout, query):
  keyboard.press(Keycode.GUI)
  keyboard.release_all()
  time.sleep(0.2)
  layout.write(query)
  time.sleep(1)
  layout.write('\n')

#
# Set some LEDs to same color
#
def set_leds(keys, arr, color):
  for i in arr:
    keys[i].set_led(*color)

#
# Make a color darker by halving its values equally
#
def darken(color):
  return (color[0] / 2, color[1] / 2, color[2] / 2)

#
# Select a layer and update keypad with its colors
#
def select_layer(keys, index):
  global current_layer
  current_layer = index

  macro_map = macros.get_macro_map()

  # A macro page
  for key in keys:
    if key.number not in constants.NAV_KEYS:
      key.set_led(*constants.COLOR_OFF)

    # Not configured
    if key.number not in macro_map[current_layer]:
      continue

    # Constant value
    key.set_led(*parse_color(macro_map[current_layer][key.number]['color']))

  # Selection keys - home, up, down
  keys[0].set_led(*darken(constants.COLOR_LIGHT_GREY))
  keys[4].set_led(*(constants.COLOR_LIGHT_GREY if current_layer > 0 else constants.COLOR_OFF))
  keys[8].set_led(*(constants.COLOR_LIGHT_GREY if current_layer < (macros.get_num_layers() - 1) else constants.COLOR_OFF))
  
#
# Get the current layer index
#
def get_current_layer():
  return current_layer

#
# Parse color from value, either a 'constants' item or rgb
#
def parse_color(color):
  if 'COLOR_' in color:
    return getattr(constants, color)
  
  # Assume RGB
  return tuple(map(int, color.split(',')))
