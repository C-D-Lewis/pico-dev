#
# Byte swap endianness for this display
#
def swap16(x):
  return (((x << 8) & 0xFF00) |
          ((x >> 8) & 0x00FF))

#
# Convert RGB888 (255) to RGB565 (31)
# Adapted from https://rgbcolorpicker.com/565
#
def rgb888_to_rgb565(red, green, blue):
  r = round((red / 255) * 31)
  g = round((green / 255) * 63)
  b = round((blue / 255) * 31)
  
  r = r << 11
  g = g << 5
  
  return swap16(r | g | b)

#
# Helper for creating colors
#
def rgb(r, g, b):
  return rgb888_to_rgb565(r, g, b)

#
# Is point inside a rect
#
def intersects(x, y, rect):
  return x > rect[0] and y > rect[1] and x < rect[0] + rect[2] and y < rect[1] + rect[3]

#
# Pad a number less than 10
#
def pad(v):
  return str(v) if v > 9 else "0{}".format(v)

