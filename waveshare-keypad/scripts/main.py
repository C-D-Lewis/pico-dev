import gc
print('main.py')
print(gc.mem_free())

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

# Area IDs
MENU_ITEM_MEDIA = 0
MENU_ITEM_APPS = 1
MENU_ITEM_WINDOWS = 2
MENU_ITEM_WEB = 3
MENU_ITEM_OTHER = 4

# Touchable areas - [x, y, w, h]
MENU_AREAS = [
  {
    'tap': [0, TOP_BAR_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'draw': [0, TOP_BAR_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'section': 'top',
  },
  {
    'tap': [0, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'draw': [0, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'section': 'top',
  },
  {
    'tap': [0, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'draw': [0, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'section': 'top',
  },
  {
    'tap': [0, TOP_BAR_HEIGHT + 3 * MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'draw': [0, 0, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'section': 'bottom',
  },
  {
    'tap': [0, TOP_BAR_HEIGHT + 4 * MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'draw': [0, MENU_ITEM_HEIGHT, MENU_WIDTH, MENU_ITEM_HEIGHT],
    'section': 'bottom',
  },
]

# Colors
COLOR_RED = util.rgb(255, 0, 0)
COLOR_DARK_RED = util.rgb(178, 0, 0)

# Other
TAP_TIMEOUT_S = 60

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
selected_menu_index = 0
is_connected = False

#
# Initialise the display
#
def init():
  LCD.bl_ctrl(100)
  LCD.fill(LCD.RED)
  LCD.show_up()
  LCD.fill(LCD.BLACK)
  LCD.show_down()

#
# Redraw everything on top
#
def draw_top():
  LCD.fill(LCD.BLACK)

  # Top bar
  LCD.fill_rect(0, 0, WIDTH, TOP_BAR_HEIGHT, COLOR_RED)
  LCD.text('========== PICO MACRO PAD ========', 25, MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.fill_rect(0, TOP_BAR_HEIGHT - 2, WIDTH, 2, LCD.BLACK)
  
  # Date and time
  now = time.localtime()
  date_str = '{}/{}/{} =='.format(now[1], now[2], now[0])
  time_str = '{}:{} =='.format(util.pad(now[3]), util.pad(now[4]))
  LCD.text(date_str, WIDTH - 100, MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.text(time_str, WIDTH - 171, MENU_TEXT_OFFSET, LCD.WHITE)

  # Wifi connected?
  LCD.text('~' if is_connected else '', 10, MENU_TEXT_OFFSET + 2, LCD.WHITE)

  # Menu categories
  LCD.fill_rect(0, TOP_BAR_HEIGHT, MENU_WIDTH, HEIGHT, COLOR_DARK_RED)
  
  # Menu selection
  selected_menu_item = MENU_AREAS[selected_menu_index]
  if selected_menu_item['section'] == 'top':
    LCD.fill_rect(*selected_menu_item['draw'], COLOR_RED)
  
  # Menu lines
  LCD.fill_rect(0, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.fill_rect(0, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  
  # Menu labels
  LCD.text('Media', 10, TOP_BAR_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.text('Apps', 10, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.text('Windows', 10, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)

  LCD.show_up()

#
# Redraw everything on top
#
def draw_bottom():
  LCD.fill(LCD.BLACK)

  # Categories
  LCD.fill_rect(0, 0, 100, HEIGHT, COLOR_DARK_RED)

  # Menu selection
  selected_menu_item = MENU_AREAS[selected_menu_index]
  if selected_menu_item['section'] == 'bottom':
    LCD.fill_rect(*selected_menu_item['draw'], COLOR_RED)
  
  # Menu lines
  LCD.fill_rect(0, 0, MENU_WIDTH, 2, LCD.BLACK)
  LCD.fill_rect(0, MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.fill_rect(0, 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  
  # Menu labels
  LCD.text('Web', 10, 17, LCD.WHITE)
  LCD.text('Other', 10, MENU_ITEM_HEIGHT + 17, LCD.WHITE)

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
# Redraw everything
#
def redraw_all():
  draw_top()
  LCD.show_up()
  draw_bottom()
  LCD.show_down()

#
# Update elements based on a touch
#
def handle_touch(x, y):
  global selected_menu_index

  # Menu tapped?
  for index, item in enumerate(MENU_AREAS):
    if util.intersects(x, y, item['tap']):
      selected_menu_index = index

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
      last_tap_time = time.time()
      is_awake = True
      LCD.bl_ctrl(100)

      touch_x = min(int((touch_pos[1] - 430) * WIDTH / 3270), WIDTH)
      touch_y = max((HEIGHT - int((touch_pos[0] - 430) * HEIGHT / 3270)), 0)
      handle_touch(touch_x, touch_y)

      redraw_all()

    # Sleep?
    if (time.time() - last_tap_time > TAP_TIMEOUT_S) and is_awake:
      is_awake = False
      LCD.bl_ctrl(0)
      draw_blank()

if __name__ == '__main__':
  init()
  main()

