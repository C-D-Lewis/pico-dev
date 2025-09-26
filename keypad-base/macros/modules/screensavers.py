import random
import time
import math

from modules import config, constants, utils

active = False
last_second_index = 0
rainbow_state = {}
starry_night_state = {
  'key': 0,
  'val': 0,
  'dir': 1,
}

#
# Go to sleep state and show screensaver
#
def start(keys):
  global active
  active = True

  for key in keys:
    key.set_led(*constants.COLOR_OFF)

#
# Return if active
#
def is_active():
  return active

#
# Set if active
#
def set_is_active(v):
  global active
  active = v

#
# Update rainbow for a given key
#
def update_rainbow(keys, key):
  rainbow_min = 8
  rainbow_max = 128

  if key not in rainbow_state:
    dist = round((key * 4) / 4) + (key % 4)
    rainbow_state[key] = {
      'rgb': [dist * 4, dist * 8, dist * 16],
      'dirs': [1, 1, 1]
    }

  rgb = rainbow_state[key]['rgb']
  dirs = rainbow_state[key]['dirs']

  # Move and bracket
  rgb[0] += (5 * dirs[0])
  rgb[1] += (5 * dirs[1])
  rgb[2] += (5 * dirs[2])
  rgb[0] = min(max(rgb[0], rainbow_min), rainbow_max)
  rgb[1] = min(max(rgb[1], rainbow_min), rainbow_max)
  rgb[2] = min(max(rgb[2], rainbow_min), rainbow_max)

  # Change direction
  if rgb[0] >= rainbow_max or rgb[0] <= rainbow_min:
    dirs[0] *= -1
  if rgb[1] >= rainbow_max or rgb[1] <= rainbow_min:
    dirs[1] *= -1
  if rgb[2] >= rainbow_max or rgb[2] <= rainbow_min:
    dirs[2] *= -1

  keys[key].set_led(rgb[0], rgb[1], rgb[2])

#
# Get clock LED digit for based on number to divide by
#
def get_clock_digit(value, divisor):
  index = math.floor(math.floor((value * 100) / divisor) / 100 * constants.TOTAL_CLOCK_DIGITS)
  return constants.CLOCK_LED_SEQ[index]

#
# Draw clock animation
#
def update_clock(keys):
  global last_second_index

  # now is array of (year, month, mday, hour, minute, second, ...)
  now = time.localtime()
  hours = (now[3] + config.TZ_OFFSET_H) % 24
  hours_12h = hours - 12 if hours >= 12 else hours
  minutes = now[4]
  seconds = now[5]

  # Positions of hands around the face
  hours_index = get_clock_digit(hours_12h, 12)
  minutes_index = get_clock_digit(minutes, 60)
  seconds_index = get_clock_digit(seconds, 60)

  # Prevent flickering by updating only for each new seconds hand position
  if seconds_index != last_second_index:
    last_second_index = seconds_index
    for key in keys:
      key.set_led(*constants.COLOR_OFF)

  # Hands
  keys[hours_index].set_led(*utils.darken(constants.COLOR_RED))
  keys[minutes_index].set_led(*utils.darken(constants.COLOR_BLUE))
  keys[seconds_index].set_led(*utils.darken(constants.COLOR_YELLOW))

#
# Update starry night screensaver
#
def update_starry_night(keys):
  # Update brightness
  starry_night_state['val'] += starry_night_state['dir']
  val = starry_night_state['val']
  keys[starry_night_state['key']].set_led(val, val, val * 3)

  # Pick new key when dark
  if starry_night_state['val'] <= 0:
    last_key = starry_night_state['key']
    next_key = last_key
    while next_key == last_key:
      next_key = random.randint(0, 15)

    starry_night_state['key'] = next_key
    starry_night_state['dir'] = 1
    starry_night_state['val'] = 1
    keys[last_key].set_led(*constants.COLOR_OFF)

  # When bright, reverse direction
  elif starry_night_state['val'] >= 64:
    starry_night_state['dir'] = -1

#
# Show clock animation if WiFI, else just the wake button
#
def update_screensaver(keys):
  now = time.localtime()
  hours_24h = (now[3] + config.TZ_OFFSET_H) % 24

  # No dazzling screensavers during inactive hours
  if hours_24h >= constants.OFF_START_H or (hours_24h >= 0 and hours_24h < constants.OFF_END_H):
    # Wasteful to write off but prevents one LED being left on when it ticks over
    for key in keys:
      key.set_led(*constants.COLOR_OFF)
    return
  elif config.SCREENSAVER == constants.SCREENSAVER_NONE:
    return
  elif config.SCREENSAVER == constants.SCREENSAVER_CLOCK and config.IS_WIFI_ENABLED:
    update_clock(keys)
  elif config.SCREENSAVER == constants.SCREENSAVER_RAINBOW:
    for key in keys:
      update_rainbow(keys, key.number)
  elif config.SCREENSAVER == constants.SCREENSAVER_SINGLE_KEY:
    keys[0].set_led(*constants.COLOR_SLEEPING)
  if config.SCREENSAVER == constants.SCREENSAVER_STARRY_NIGHT:
    update_starry_night(keys)
