# keypad-base

Scripts for the Raspberry Pi Pico W and Pimoroni RGB Keypad Base accessory.

Contains examples and libraries from Adafruit and Pimoroni, can be found here:
https://learn.pimoroni.com/article/circuitpython-and-keybow-2040#pmk-on-pico-rgb-keypad


# Setup

1. Install the Adafruit CircuitPython firmware from `firmware` to the Pico W by
   copying the file to the USB drive presented when plugging in the Pico W and
   holding the button.
2. Copy the keypad required libraries from `lib` to `lib` on the Pico W.
3. Copy an example from `examples` as `code.py` to test all is working.
4. Choose a script from this repository, such as `macros` to run.

## Macros

The main script for keypad dev is the multi-layer macros project.

More complex version of `shortcuts.py` with multiple layers of macros available.

The macros available are defined in a `macros.json` file independent of any code
file. `macros.example.json` can be used as a starting point for:

* Layer 0 - Media controls
  * Prev/play/next
  * Vol down/mute/Vol up
  * Discord mute (Ctrl+Shift+M)
* Layer 1 - Numpad
* Layer 2 - Applications
  * Spotify/Steam/Discord
  * Firefox
* Layer 3 - Windows
  * Task Manager/Explorer
  * Sleep/Reboot/Shutdown
* Layer 4 - Other
  * Shadowplay GUI/Save buffer/Toggle recording
  * Toggle screensaver/Sleep keypad

Left column contains layer selection buttons:

* Home
* Previous layer
* Next layer

Copy all files from `macros` and configure `settings.toml` and `macros.json`.

> Note: Colors from `constants.py` can be used by specifying their name, or else
> `"r,g,b"` string can be used. Keycodes and ConsumerControlCodes can be used in
> a similar manner by using their names as mentioned in those modules'
> documentation.

## Other scripts

### `shortcuts.py` - Media and keyboard shortcuts.

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


### `wifi_test.py` - Test Pico W WiFi connection

Test WiFi connection and/or credentials.

Requires `settings.toml` with `WIFI_SSID` and `WIFI_PASSWORD`.

Example:
```
WIFI_SSID=""
WIFI_PASSWORD=""
```
