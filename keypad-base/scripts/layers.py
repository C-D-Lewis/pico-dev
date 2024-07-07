import gc
print('main.py')
print(gc.mem_free())

def log():
    f = open('data.txt', 'w')
    f.write('got here!')
    f.close()

import time
import os
import lcd_lib
import util

# Geometry
WIDTH = 480
HALF_HEIGHT = 160
HEIGHT = 2* HALF_HEIGHT
TOP_BAR_HEIGHT = 40
TOP_H_HEIGHT = HALF_HEIGHT - TOP_BAR_HEIGHT
BOTTOM_H_HEIGHT = HALF_HEIGHT
MENU_WIDTH = 100
MENU_ITEM_HEIGHT = round(TOP_H_HEIGHT / 3)
MENU_TEXT_OFFSET = 17

# Touchable areas - [x, y, w, h]
TAP_AREAS = [
  # Media
  {
    'area': [0, TOP_BAR_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'handler': lambda: on_area_tapped(0),
  },
]

# Colors
COLOR_RED = util.rgb(255, 0, 0)
COLOR_DARK_RED = util.rgb(178, 0, 0)

# Other
TAP_TIMEOUT_S = 10

#
# This LCD module has drawing split into two halves, top and bottom.
#
# After a fill(), one of show_up() or show_down() will then show whatever was
# painted onto that half.
#
# Touch coordinates are true, however.
LCD = lcd_lib.LCD_3inch5()

# State
is_awake = True
last_tap_time = time.time()

#
# Initialise the display
#
def init():
  LCD.bl_ctrl(50)
  LCD.fill(LCD.RED)
  LCD.show_up()
  LCD.fill(LCD.BLACK)
  LCD.show_down()
  log()

#
# Redraw everything on top
#
def draw_top():
  LCD.fill(LCD.BLACK)

  # Top bar
  LCD.fill_rect(0, 0, WIDTH, TOP_BAR_HEIGHT, COLOR_RED)
  LCD.text("PICO MACRO PAD", 15, MENU_TEXT_OFFSET, LCD.WHITE)
  # Date and time
  now = time.localtime()
  date_str = "{}/{}/{}".format(now[1], now[2], now[0])
  time_str = "{}:{} --".format(util.pad(now[3]), util.pad(now[4]))
  LCD.text(date_str, WIDTH - 75, MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.text(time_str, WIDTH - 146, MENU_TEXT_OFFSET, LCD.WHITE)

  # Categories
  LCD.fill_rect(0, TOP_BAR_HEIGHT, MENU_WIDTH, HEIGHT, COLOR_DARK_RED)
  # Lines
  LCD.fill_rect(0, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.fill_rect(0, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  # Labels
  LCD.text("Media", 10, TOP_BAR_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.text("Apps", 10, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.text("Windows", 10, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)

  LCD.show_up()

#
# Redraw everything on top
#
def draw_bottom():
  LCD.fill(LCD.BLACK)

  # Categories
  LCD.fill_rect(0, 0, 100, HEIGHT, COLOR_DARK_RED)
  # Lines
  LCD.fill_rect(0, 0, MENU_WIDTH, 2, LCD.BLACK)
  LCD.fill_rect(0, MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.fill_rect(0, 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  # Labels
  LCD.text("Web", 10, 17, LCD.WHITE)
  LCD.text("Other", 10, MENU_ITEM_HEIGHT + 17, LCD.WHITE)

  LCD.show_down()

#
# Draw a black screen
#
def draw_blank():
  LCD.fill(LCD.BLACK)
  LCD.show_up()
  LCD.fill(LCD.BLACK)
  LCD.show_down()

#
# Update elements based on a touch
#
def handle_touch(x, y):
  # Menu?
  for index, item in enumerate(TAP_AREAS):
    if util.intersects(x, y, item['area']):
      print("tap {}".format(index))
      item['handler']()

  return

#
# When an area is tapped, do something specific
#
def on_area_tapped(index):
  print(index)

#
# The main function
#
def main():
  global last_tap_time
  global is_awake

  draw_top()
  draw_bottom()

  while True:
    time.sleep(0.1)

    # Wait for touch
    touch_pos = LCD.touch_get()
    if touch_pos != None:
      touch_x = min(int((touch_pos[1] - 430) * WIDTH / 3270), WIDTH)
      touch_y = max((HEIGHT - int((touch_pos[0] - 430) * HEIGHT / 3270)), 0)

      if (touch_y > HALF_HEIGHT):
        touch_y = touch_y - HALF_HEIGHT
      handle_touch(touch_x, touch_y)
      last_tap_time = time.time()
      is_awake = True

      # Redraw everything
      draw_top()
      LCD.show_up()
      draw_bottom()
      LCD.show_down()

    # Sleep?
    if (time.time() - last_tap_time > TAP_TIMEOUT_S) and is_awake:
      is_awake = False
      draw_blank()
      continue

if __name__ == "__main__":
  init()
  main()

