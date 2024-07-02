from machine import Pin, SPI, PWM
import framebuf
import time

LCD_DC = 8
LCD_CS = 9
LCD_SCK = 10
LCD_MOSI = 11
LCD_MISO = 12
LCD_BL = 13
LCD_RST = 15
TP_CS = 16
TP_IRQ = 17

class LCD_3inch5(framebuf.FrameBuffer):
  def __init__(self):
    self.RED = 0x07E0
    self.GREEN = 0x001F
    self.BLUE = 0xF800
    self.WHITE = 0xFFFF
    self.BLACK = 0x0000

    self.rotate = 270  # Set the rotation Angle to 0°, 90°, 180° and 270°

    if self.rotate == 0 or self.rotate == 180:
      self.width = 320
      self.height = 240
    else:
      self.width = 480
      self.height = 160

    self.cs = Pin(LCD_CS, Pin.OUT)
    self.rst = Pin(LCD_RST, Pin.OUT)
    self.dc = Pin(LCD_DC, Pin.OUT)

    self.tp_cs = Pin(TP_CS, Pin.OUT)
    self.irq = Pin(TP_IRQ, Pin.IN)

    self.cs(1)
    self.dc(1)
    self.rst(1)
    self.tp_cs(1)
    self.spi = SPI(1, 6_000_000)
    print(self.spi)
    self.spi = SPI(
      1,
      baudrate=40_000_000,
      sck=Pin(LCD_SCK),
      mosi=Pin(LCD_MOSI),
      miso=Pin(LCD_MISO),
    )
    print(self.spi)
    self.buffer = bytearray(self.height * self.width * 2)
    super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
    self.init_display()

  def write_cmd(self, cmd):
    self.cs(1)
    self.dc(0)
    self.cs(0)
    self.spi.write(bytearray([cmd]))
    self.cs(1)

  def write_data(self, buf):
    self.cs(1)
    self.dc(1)
    self.cs(0)
    # self.spi.write(bytearray([0X00]))
    self.spi.write(bytearray([buf]))
    self.cs(1)

  def init_display(self):
    """Initialize dispaly"""
    self.rst(1)
    time.sleep_ms(5)
    self.rst(0)
    time.sleep_ms(10)
    self.rst(1)
    time.sleep_ms(5)
    self.write_cmd(0x21)

    self.write_cmd(0xC2)
    self.write_data(0x33)

    self.write_cmd(0xC5)
    self.write_data(0x00)
    self.write_data(0x1E)
    self.write_data(0x80)

    self.write_cmd(0xB1)
    self.write_data(0xB0)

    self.write_cmd(0xE0)
    self.write_data(0x00)
    self.write_data(0x13)
    self.write_data(0x18)
    self.write_data(0x04)
    self.write_data(0x0F)
    self.write_data(0x06)
    self.write_data(0x3A)
    self.write_data(0x56)
    self.write_data(0x4D)
    self.write_data(0x03)
    self.write_data(0x0A)
    self.write_data(0x06)
    self.write_data(0x30)
    self.write_data(0x3E)
    self.write_data(0x0F)

    self.write_cmd(0xE1)
    self.write_data(0x00)
    self.write_data(0x13)
    self.write_data(0x18)
    self.write_data(0x01)
    self.write_data(0x11)
    self.write_data(0x06)
    self.write_data(0x38)
    self.write_data(0x34)
    self.write_data(0x4D)
    self.write_data(0x06)
    self.write_data(0x0D)
    self.write_data(0x0B)
    self.write_data(0x31)
    self.write_data(0x37)
    self.write_data(0x0F)

    self.write_cmd(0x3A)
    self.write_data(0x55)

    self.write_cmd(0x11)
    time.sleep_ms(120)
    self.write_cmd(0x29)

    self.write_cmd(0xB6)
    self.write_data(0x00)
    self.write_data(0x62)

    self.write_cmd(0x36)  # Sets the memory access mode for rotation
    if self.rotate == 0:
      self.write_data(0x88)
    elif self.rotate == 180:
      self.write_data(0x48)
    elif self.rotate == 90:
      self.write_data(0xE8)
    else:
      self.write_data(0x28)

  def show_up(self):
    if self.rotate == 0 or self.rotate == 180:
      self.write_cmd(0x2A)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x01)
      self.write_data(0x3F)

      self.write_cmd(0x2B)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0xEF)
    else:
      self.write_cmd(0x2A)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x01)
      self.write_data(0xDF)

      self.write_cmd(0x2B)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x9F)

    self.write_cmd(0x2C)

    self.cs(1)
    self.dc(1)
    self.cs(0)
    self.spi.write(self.buffer)
    self.cs(1)

  def show_down(self):
    if self.rotate == 0 or self.rotate == 180:
      self.write_cmd(0x2A)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x01)
      self.write_data(0x3F)

      self.write_cmd(0x2B)
      self.write_data(0x00)
      self.write_data(0xF0)
      self.write_data(0x01)
      self.write_data(0xDF)
    else:
      self.write_cmd(0x2A)
      self.write_data(0x00)
      self.write_data(0x00)
      self.write_data(0x01)
      self.write_data(0xDF)

      self.write_cmd(0x2B)
      self.write_data(0x00)
      self.write_data(0xA0)
      self.write_data(0x01)
      self.write_data(0x3F)

    self.write_cmd(0x2C)

    self.cs(1)
    self.dc(1)
    self.cs(0)
    self.spi.write(self.buffer)
    self.cs(1)

  def bl_ctrl(self, duty):
    pwm = PWM(Pin(LCD_BL))
    pwm.freq(1000)
    if duty >= 100:
      pwm.duty_u16(65535)
    else:
      pwm.duty_u16(655 * duty)

  def touch_get(self):
    if self.irq() == 0:
      self.spi = SPI(
        1, 4_000_000, sck=Pin(LCD_SCK), mosi=Pin(LCD_MOSI), miso=Pin(LCD_MISO)
      )
      self.tp_cs(0)
      X_Point = 0
      Y_Point = 0
      for i in range(0, 3):
        self.spi.write(bytearray([0xD0]))
        Read_date = self.spi.read(2)
        time.sleep_us(10)
        X_Point = X_Point + (((Read_date[0] << 8) + Read_date[1]) >> 3)

        self.spi.write(bytearray([0x90]))
        Read_date = self.spi.read(2)
        Y_Point = Y_Point + (((Read_date[0] << 8) + Read_date[1]) >> 3)

      X_Point = X_Point / 3
      Y_Point = Y_Point / 3

      self.tp_cs(1)
      self.spi = SPI(
        1, 40_000_000, sck=Pin(LCD_SCK), mosi=Pin(LCD_MOSI), miso=Pin(LCD_MISO)
      )
      Result_list = [X_Point, Y_Point]
      # print(Result_list)
      return Result_list