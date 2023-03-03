from pmk import PMK
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Set up Keybow
keybow = PMK(Hardware())
keys = keybow.keys
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

# Shortcuts:
# 0: vol up, 1: prev, 2: play/pause, 3: next
# 4: vol down,
# 8: -
# 12: mute,

# ConsumerControlCode.SCAN_PREVIOUS_TRACK
# ConsumerControlCode.PLAY_PAUSE
# ConsumerControlCode.SCAN_NEXT_TRACK

# A map of keycodes that will be mapped sequentially to each of the keys, 0-15
keymap = {
  0: {
    'type': 'control',
    'code': ConsumerControlCode.VOLUME_INCREMENT,
    'inactive': (64, 64, 0),
    'active': (255, 255, 0)
  },
  1: {
    'type': 'control',
    'code': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
    'inactive': (0, 0, 64),
    'active': (0, 0, 255)
  },
  2: {
    'type': 'control',
    'code': ConsumerControlCode.PLAY_PAUSE,
    'inactive': (0, 64, 0),
    'active': (0, 255, 0)
  },
  3: {
    'type': 'control',
    'code': ConsumerControlCode.SCAN_NEXT_TRACK,
    'inactive': (0, 0, 64),
    'active': (0, 0, 255)
  },
  4: {
    'type': 'control',
    'code': ConsumerControlCode.VOLUME_DECREMENT,
    'inactive': (64, 64, 0),
    'active': (255, 255, 0)
  },
  12: {
    'type': 'control',
    'code': ConsumerControlCode.MUTE,
    'inactive': (64, 0, 0),
    'active': (255, 0, 0)
  }
}

# Attach handler functions to all of the keys
for key in keys:
  if key.number not in keymap:
    continue
  config = keymap[key.number]

  # Set initial color
  key.set_led(*config['inactive'])

  # When pressed
  @keybow.on_press(key)
  def press_handler(key):
    config = keymap[key.number]

    if config['type'] == 'control':
      consumer_control.send(config['code'])
    if config['type'] == 'key':
      keyboard.send(config['code'])
    key.set_led(*config['active'])

  # When released
  @keybow.on_release(key)
  def release_handler(key):
    config = keymap[key.number]
    key.set_led(*config['inactive'])

while True:
  keybow.update()
