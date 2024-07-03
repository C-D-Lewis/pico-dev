import time
import os
import lcd_lib
import util

WIDTH = 480
HALF_HEIGHT = 160
HEIGHT = 2* HALF_HEIGHT
TOP_BAR_HEIGHT = 40
TOP_H_HEIGHT = HALF_HEIGHT - TOP_BAR_HEIGHT
BOTTOM_H_HEIGHT = HALF_HEIGHT

COLOR_RED = util.rgb(255, 0, 0)
COLOR_DARK_RED = util.rgb(178, 0, 0)

#
# This LCD module has drawing split into two halves, top and bottom.
#
# After a fill(), one of show_up() or show_down() will then show whatever was
# painted onto that half.
#
# Touch coordinates are true, however.
LCD = lcd_lib.LCD_3inch5()

#
# Initialise the display
#
def init():
  LCD.bl_ctrl(50)
  LCD.fill(LCD.BLACK)
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
  LCD.text("Macro Pad", 20, 17, LCD.WHITE)

  # Categories
  LCD.fill_rect(0, TOP_BAR_HEIGHT, 100, HEIGHT, COLOR_DARK_RED)

  LCD.show_up()

#
# Redraw everything on top
#
def draw_bottom():
  LCD.fill(LCD.BLACK)

  # Categories
  LCD.fill_rect(0, 0, 100, HEIGHT, COLOR_DARK_RED)

  LCD.show_down()

#
# Update elements based on a touch
#
def handle_touch(x, y):
  # Was a category touched?
  return

#
# The main function
#
def main():
  draw_top()
  draw_bottom()

  # while True:
  #   time.sleep(0.1)

  #   # Wait for touch
  #   touch_pos = LCD.touch_get()
  #   if touch_pos != None:
  #     touch_x = min(int((touch_pos[1] - 430) * WIDTH / 3270), WIDTH)
  #     touch_y = max((HEIGHT - int((touch_pos[0] - 430) * HEIGHT / 3270)), 0)

  #     if (touch_y > HALF_HEIGHT):
  #       touch_y = touch_y - HALF_HEIGHT
  #     handle_touch(touch_x, touch_y)

  #     # Redraw everything
  #     draw_top()
  #     LCD.show_up()
  #     draw_bottom()
  #     LCD.show_down()

if __name__ == "__main__":
  init()
  main()
