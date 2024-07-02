# TODO Get these params straight...
def brg_to_rgb565(blue, red, green):
  # Convert each color component to a 5-bit value (lower bits discarded)
  r = (red & 0xF8) << 8
  g = (green & 0xFC) << 3
  b = blue >> 3

  # Combine the components into a single 16-bit RGB565 value
  return r | g | b

# TODO Get these params straight...
def rgb(red, green, blue):
  return brg_to_rgb565(green, blue, red)
