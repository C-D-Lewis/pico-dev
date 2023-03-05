from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from time import sleep

# Set up Keybow
keybow = PMK(Hardware())
keys = keybow.keys
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

layer_index = 0

# Map of keys on each layer
KEY_MAP = {
  # Media
  0: {
    1: {
      'control_code': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
      'color': (0, 0, 64)
    },
    2: {
      'control_code': ConsumerControlCode.PLAY_PAUSE,
      'color': (0, 64, 0)
    },
    3: {
      'control_code': ConsumerControlCode.SCAN_NEXT_TRACK,
      'color': (0, 0, 64)
    },
    5: {
      'control_code': ConsumerControlCode.VOLUME_DECREMENT,
      'color': (64, 64, 0)
    },
    6: {
      'control_code': ConsumerControlCode.MUTE,
      'color': (64, 0, 0)
    },
    7: {
      'control_code': ConsumerControlCode.VOLUME_INCREMENT,
      'color': (64, 64, 0)
    },
    # Mute Discord mic
    13: {
      'combo': (Keycode.CONTROL, Keycode.M),
      'color': (64, 0, 0)
    }
  },
  # Applications
  1: {
    1: {
      'custom': lambda: launch_program('spotify'),
      'color': (0, 64, 0)
    },
    2: {
      'custom': lambda: launch_program('steam'),
      'color': (0, 0, 16)
    },
    3: {
      'custom': lambda: launch_program('discord'),
      'color': (0, 32, 64)
    }
  },
  # Unused
  2: {},
  # System
  3: {
    1: {
      'combo': (Keycode.CONTROL, Keycode.SHIFT, Keycode.ESCAPE),
      'color': (79, 11, 103)
    },
    2: {
      'combo': (Keycode.GUI, Keycode.E),
      'color': (64, 64, 0)
    },
    14: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.S],
      'color': (0, 0, 32)
    },
    15: {
      'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.U],
      'color': (32, 0, 0)
    }
  }
}
# Index selection key numbers
INDEX_SELECTION_KEYS = (0, 4, 8, 12)
# Off color
COLOR_OFF = (0, 0, 0)
# Flash color
COLOR_FLASH = (128, 128, 128)
# White when selected layer
COLOR_SELECTED_LAYER = (32, 32, 32)
# White for unselected layer
COLOR_UNSELECTED_LAYER = (4, 4, 4)

#
# Launch a program via Start menu query
#
def launch_program(query):
  keyboard.press(Keycode.GUI)
  keyboard.release_all()
  sleep(0.2)
  layout.write(query)
  sleep(1)
  layout.write('\n')

#
# Flash a key to confirm an action.
#
def flash_confirm(key):
  key.set_led(*COLOR_FLASH)
  sleep(0.05)
  key.set_led(*COLOR_OFF)
  sleep(0.05)
  key.set_led(*COLOR_FLASH)
  sleep(0.05)
  key.set_led(*COLOR_OFF)

#
# Attach handler functions to all of the keys for this layer.
#
def set_layer(new_layer):
  global layer_index
  layer_index = new_layer

  # Update colors
  for key in keys:
    key.set_led(*COLOR_OFF)

    # Update layer indicator
    if key.number in INDEX_SELECTION_KEYS:
      key.set_led(*COLOR_UNSELECTED_LAYER)
      if key.number / 4 == layer_index:
        key.set_led(*COLOR_SELECTED_LAYER)

    # Not configured
    if key.number not in KEY_MAP[layer_index]:
      continue

    key.set_led(*KEY_MAP[layer_index][key.number]['color'])

#
# Handle a key press event
#
def handle_key_press(key):
  # Layer select
  for i in INDEX_SELECTION_KEYS:
    if key.number == i:
      set_layer(i / 4)
      key.set_led(*COLOR_SELECTED_LAYER)
      return

  # Layer configured key
  config = KEY_MAP[layer_index][key.number]

  # Control code
  if 'control_code' in config:
    consumer_control.send(config['control_code'])
  
  # Text string
  if 'text' in config:
    layout.write(config['text'])
  
  # Key combinationn
  if 'combo' in config:
    keyboard.press(*config['combo'])
    keyboard.release_all()

  # Sequence of key combinations
  if 'sequence' in config:
    for item in config['sequence']:
      if isinstance(item, tuple):
        keyboard.press(*item)
      else:
        keyboard.press(item)
      sleep(0.2)
      keyboard.release_all()

  # Custom function
  if 'custom' in config:
    config['custom']()

# Attach handlers
for key in keys:
  @keybow.on_press(key)
  def press_handler(key):
    # Not configured
    if key.number not in KEY_MAP[layer_index] and key.number not in INDEX_SELECTION_KEYS:
      return

    handle_key_press(key)
    flash_confirm(key)

  @keybow.on_release(key)
  def release_handler(key):
    # Not configured
    if key.number not in KEY_MAP[layer_index] and key.number not in INDEX_SELECTION_KEYS:
      return

    # Layer selection key
    if key.number in INDEX_SELECTION_KEYS:
      key.set_led(*COLOR_SELECTED_LAYER if key.number / 4 == layer_index else COLOR_UNSELECTED_LAYER)
      return

    # Layer configured key
    key.set_led(*KEY_MAP[layer_index][key.number]['color'])

def main():
  set_layer(0)
  while True:
    keybow.update()

main()
