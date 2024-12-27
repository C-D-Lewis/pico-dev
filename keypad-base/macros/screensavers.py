# Local modules
import constants

active = False
disabled = False

#
# Go to sleep state and show screensaver
#
def start_screensaver(keys):
  global active
  active = True

  # select_layer(0)

  for key in keys:
    key.set_led(*constants.COLOR_OFF)

#
# Toggle stay awake mode
#
def toggle_screensaver_disabled(keys):
  global disabled
  disabled = not disabled

  # if disabled:
  #   select_layer(0)
  # else:
  start_screensaver(keys)

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
# Return if disabled
#
def is_disabled():
  return disabled
