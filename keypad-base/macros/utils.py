from adafruit_hid.keycode import Keycode
import time

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
