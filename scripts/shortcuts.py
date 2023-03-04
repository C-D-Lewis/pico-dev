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

KEY_MAP = {
  0: {
    'control_code': ConsumerControlCode.VOLUME_INCREMENT,
    'color': (64, 64, 0)
  },
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
  4: {
    'control_code': ConsumerControlCode.VOLUME_DECREMENT,
    'color': (64, 64, 0)
  },
  6: {
    'control_code': ConsumerControlCode.MUTE,
    'color': (64, 0, 0)
  },
  12: {
    'combo': (Keycode.CONTROL, Keycode.M),
    'color': (64, 0, 0)
  },
  14: {
    'sequence': [(Keycode.GUI, Keycode.X), Keycode.U, Keycode.S],
    'color': (0, 0, 32)
  },
  15: {
    'combo': (Keycode.CONTROL, Keycode.SHIFT, Keycode.ESCAPE),
    'color': (79, 11, 103)
  }
}

#
# Flash a key to confirm an action.
#
def flash_confirm(key):
  key.set_led(128, 128, 128)
  sleep(0.05)
  key.set_led(0, 0, 0)
  sleep(0.05)
  key.set_led(128, 128, 128)
  sleep(0.05)
  key.set_led(0, 0, 0)

#
# Handle a key press event
#
def handle_key_press(key):
  config = KEY_MAP[key.number]

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

# Attach handler functions to all of the keys
for key in keys:
  if key.number not in KEY_MAP:
    continue
  config = KEY_MAP[key.number]
  key.set_led(*config['color'])

  @keybow.on_press(key)
  def press_handler(key):
    handle_key_press(key)
    flash_confirm(key)

  @keybow.on_release(key)
  def release_handler(key):
    key.set_led(*KEY_MAP[key.number]['color'])

# Loop input detection forever
while True:
  keybow.update()
