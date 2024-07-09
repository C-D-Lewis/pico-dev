import gc
print(gc.mem_free())

import math
import lcd_lib
import util

# Geometry
WIDTH = 480
HALF_HEIGHT = 160
HEIGHT = 2* HALF_HEIGHT
COLUMNS = 32
X_COLOR_INCREMENT = math.floor(255 / COLUMNS)
SWATCH_SIZE = math.floor(WIDTH / COLUMNS)
ROWS = math.floor(HALF_HEIGHT / SWATCH_SIZE)
Y_COLOR_INCREMENT = math.floor(255 / ROWS)

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
def init_display():
  LCD.bl_ctrl(100)
  LCD.fill(LCD.BLACK)
  LCD.show_up()
  LCD.fill(LCD.BLACK)
  LCD.show_down()

#
# Redraw everything on top
#
def draw_top():
  LCD.fill(LCD.BLACK)

  # Half of the colors
  r = 0
  g = 0
  b = 0
  x = 0
  y = 0
  
  # Red
  while r < 255:
    LCD.fill_rect(x, y, SWATCH_SIZE, SWATCH_SIZE, util.rgb(r, g, b))
    r += X_COLOR_INCREMENT
    x += SWATCH_SIZE

  # Green
  x = 0
  y += SWATCH_SIZE
  r = 0
  while g < 255:
    LCD.fill_rect(x, y, SWATCH_SIZE, SWATCH_SIZE, util.rgb(r, g, b))
    g += X_COLOR_INCREMENT
    x += SWATCH_SIZE
    
  # Blue
  x = 0
  y += SWATCH_SIZE
  g = 0
  while b < 255:
    LCD.fill_rect(x, y, SWATCH_SIZE, SWATCH_SIZE, util.rgb(r, g, b))
    b += X_COLOR_INCREMENT
    x += SWATCH_SIZE

  LCD.show_up()

#
# Redraw everything on top
#
def draw_bottom():
  LCD.fill(LCD.BLACK)

  r = 0
  g = 0
  b = 0

  # Traverse the space
  for y in range(0, ROWS):
    r = 0
    g += Y_COLOR_INCREMENT

    for x in range(0, COLUMNS):
      LCD.fill_rect(x * SWATCH_SIZE, y * SWATCH_SIZE, SWATCH_SIZE, SWATCH_SIZE, util.rgb(r, g, b))
      r += X_COLOR_INCREMENT

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
# The main function
#
def main():
  draw_top()
  draw_bottom()

if __name__ == '__main__':
  init_display()
  main()


