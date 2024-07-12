import gc
print(gc.mem_free())

import time
import os
import lcd_lib
import util
import network
import socket
import machine
import math

# Geometry
WIDTH = 480
HALF_HEIGHT = 160
HEIGHT = 2* HALF_HEIGHT
TOP_BAR_HEIGHT = 40
TOP_HALF_HEIGHT = HALF_HEIGHT - TOP_BAR_HEIGHT
BOTTOM_H_HEIGHT = HALF_HEIGHT
MENU_WIDTH = 100
MENU_ITEM_HEIGHT = round(TOP_HALF_HEIGHT / 3)
MENU_TEXT_OFFSET = 17
BUTTON_WIDTH = 80
BUTTON_HEIGHT = 50

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
INFREQUENT_INTERVAL_S = 10

# This LCD module has drawing split into two halves, top and bottom.
#
# After a fill(), one of show_up() or show_down() will then show whatever was
# painted onto that half.
#
# Touch coordinates are true, however.
LCD = lcd_lib.LCD_3inch5()

# State
wlan = None
is_awake = True
last_tap_time = time.time()
last_infrequent_time = time.time()
selected_menu_index = 0
is_connected = False
config = {}

#
# Load config
#
def load_config():
  global config

  f = open('config.ini', 'r')
  content = f.read()
  lines = content.replace('\r', '').split("\n")
  for l in lines:
    l = l.strip()
  ssid = lines[0].split('=')[1]
  password = lines[1].split('=')[1]

  config = {
    'ssid': ssid,
    'password': password
  }
  print(config)

#
# Connect to Wifi
#
def connect():
  global wlan

  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(config['ssid'], config['password'])

#
# Initialise the display
#
def init_display():
  LCD.bl_ctrl(100)
  LCD.fill(LCD.BLACK)
  LCD.show_up()
  LCD.fill(LCD.BLACK)
  LCD.show_down()

#
# Draw grid for buttons
#
def draw_button_grid(y_start):
  line_w = 2
  num_rows = 2
  num_cols = 4
  x_interval = round((WIDTH - MENU_WIDTH) / num_cols)
  y_interval = round(TOP_HALF_HEIGHT / num_rows)

  # Vertical lines
  for col in range(1, num_cols):
    x = MENU_WIDTH + (col * x_interval)
    y = y_start
    LCD.fill_rect(x, y, 2, TOP_HALF_HEIGHT, LCD.WHITE)

  # Horizontal lines
  r_start = 1 if y_start == TOP_BAR_HEIGHT else 0
  for row in range(r_start, num_rows):
    y = y_start + (row * y_interval)
    LCD.fill_rect(MENU_WIDTH, y, WIDTH - MENU_WIDTH, 2, LCD.WHITE)

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
  LCD.text('~' if is_connected else ' ', 10, MENU_TEXT_OFFSET + 2, LCD.WHITE)

  LCD.fill_rect(0, TOP_BAR_HEIGHT, MENU_WIDTH, HEIGHT, COLOR_DARK_RED)

  # Menu selection
  selected_menu_item = MENU_AREAS[selected_menu_index]
  if selected_menu_item['section'] == 'top':
    LCD.fill_rect(*selected_menu_item['draw'], COLOR_RED)

  # Menu items
  LCD.text('Media', 10, TOP_BAR_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.fill_rect(0, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.text('Apps', 10, TOP_BAR_HEIGHT + MENU_ITEM_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)
  LCD.fill_rect(0, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.text('Windows', 10, TOP_BAR_HEIGHT + 2 * MENU_ITEM_HEIGHT + MENU_TEXT_OFFSET, LCD.WHITE)

  # Grid of buttons
  draw_button_grid(TOP_BAR_HEIGHT)

  LCD.show_up()

#
# Redraw everything on top
#
def draw_bottom():
  LCD.fill(LCD.BLACK)

  LCD.fill_rect(0, 0, 100, HEIGHT, COLOR_DARK_RED)

  # Menu selection
  selected_menu_item = MENU_AREAS[selected_menu_index]
  if selected_menu_item['section'] == 'bottom':
    LCD.fill_rect(*selected_menu_item['draw'], COLOR_RED)

  # Menu items
  LCD.fill_rect(0, 0, MENU_WIDTH, 2, LCD.BLACK)
  LCD.text('Web', 10, 17, LCD.WHITE)
  LCD.fill_rect(0, MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)
  LCD.text('Other', 10, MENU_ITEM_HEIGHT + 17, LCD.WHITE)
  LCD.fill_rect(0, 2 * MENU_ITEM_HEIGHT, MENU_WIDTH, 2, LCD.BLACK)

  # Grid of buttons
  draw_button_grid(0)

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
# Do something less frequently than 10Hz
#
def on_infrequent_update():
  global is_connected

  if wlan:
    is_connected = wlan.isconnected()
    redraw_all()

#
# The main function
#
def loop():
  global last_tap_time
  global is_awake
  global last_infrequent_time

  draw_top()
  draw_bottom()

  while True:
    time.sleep(0.1)

    now = time.time()
    if now - last_infrequent_time > INFREQUENT_INTERVAL_S:
      last_infrequent_time = now
      on_infrequent_update()

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
  load_config()
  init_display()
  redraw_all()
  connect()
  loop()
