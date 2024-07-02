import time
import os
import lcd_lib

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
# The main function
#
def main():
  # color BRG
  LCD.fill(LCD.BLACK)
  LCD.fill_rect(140, 5, 200, 30, LCD.RED)
  LCD.text("Raspberry Pi Pico", 170, 17, LCD.WHITE)
  LCD.show_up()

  # Wait for touch
  while True:
    get = LCD.touch_get()

    # Touch was detected
    if get != None:
      X_Point = int((get[1] - 430) * 480 / 3270)
      if X_Point > 480:
        X_Point = 480
      elif X_Point < 0:
        X_Point = 0
      Y_Point = 320 - int((get[0] - 430) * 320 / 3270)

      if Y_Point > 220:
        LCD.fill(LCD.WHITE)
        if X_Point < 120:
          LCD.fill_rect(0, 60, 120, 100, LCD.RED)
          LCD.text("Button0", 20, 110, LCD.WHITE)
        elif X_Point < 240:
          LCD.fill_rect(120, 60, 120, 100, LCD.RED)
          LCD.text("Button1", 150, 110, LCD.WHITE)
        elif X_Point < 360:
          LCD.fill_rect(240, 60, 120, 100, LCD.RED)
          LCD.text("Button2", 270, 110, LCD.WHITE)
        else:
          LCD.fill_rect(360, 60, 120, 100, LCD.RED)
          LCD.text("Button3", 400, 110, LCD.WHITE)
    # No touch state
    else:
      LCD.fill(LCD.WHITE)
      LCD.text("Button0", 20, 110, LCD.BLACK)
      LCD.text("Button1", 150, 110, LCD.BLACK)
      LCD.text("Button2", 270, 110, LCD.BLACK)
      LCD.text("Button3", 400, 110, LCD.BLACK)
    
    # Draw both halves
    time.sleep(0.1)
    LCD.show_down()
    
if __name__ == "__main__":
  init()
  main()
