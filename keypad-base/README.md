# keypad-base

Scripts for the Raspberry Pi Pico W and Pimoroni RGB Keypad Base accessory.

Contains examples and libraries from Adafruit and Pimoroni, can be found here:
https://learn.pimoroni.com/article/circuitpython-and-keybow-2040#pmk-on-pico-rgb-keypad


# Setup

1. Install the Adafruit CircuitPython firmware from `firmware` to the Pico W.
2. Copy the keypad required libraries from `lib` to `lib` on the Pico W.
3. Copy an example from `examples` as `code.py` to test all is working.
4. Choose a script from this repository, such as `macros.py` as `code.py` to run.


# Scripts

## `shortcuts.py` - Media and keyboard shortcuts.

Very simple version of `macros.py` with fewer options available.

| Key | Function | Color |
|-----|----------|-------|
| 1 | Previous track | Blue |
| 2 | Play/pause | Green |
| 3 | Next track | Blue |
| 5 | Volume Down | Yellow |
| 6 | Mute volume | Red |
| 7 | Volume up | Yellow |
| 12 | Discord mute (Ctrl+Shift+M) | Red |
| 15 | Sleep PC | Dark blue |

## `macros.py` - Multi-layer functions.

More complex version of `shortcuts.py` with multiple layers of macros available.

* Layer 1 - Media controls
  * Prev/play/next
  * Vol down/mute/Vol up
  * Discord mute (Ctrl+Shift+M)
* Layer 2 - Applications
  * Spotify/Steam/Discord
* Layer 3 - Windows
  * Task Manager/Explorer
  * Sleep/Reboot/Shutdown
* Layer 4 - Other
  * Rainbow demo
  * Toggle screensaver/Sleep keypad

## `wifi_test.py` - Test Pico W WiFi connection

Test WiFi connection and/or credentials.

Requires `settings.toml` with `WIFI_SSID` and `WIFI_PASSWORD`.

Example:
```
WIFI_SSID=""
WIFI_PASSWORD=""
```
