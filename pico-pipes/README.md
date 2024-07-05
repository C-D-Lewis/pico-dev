# pico-pipes

Playing MIDI files on stepper motors via Raspberry Pi Pico. A Python script
using `pretty_midi` loads a MIDI file and generates a `notes.h` C header file
defining the notes as a table of `float` tracks, pitches, and timings.


## Setup

Install dependencies:

```shell
pip3 install --user pretty_midi
```


## Prepare a MIDI file

First, compile the MIDI into an importable Python table of note events:

```shell
python3 compile.py $midiPath $trackList
```

Where `$trackList` is a comma-separated list of MIDI instrument tracks to play.
A list will be shown when `compile.py` is run with the names and number of notes
to aid selection. For example:

```shell
python3 compile.py midi/still_alive.mid 0,1
```


## Prepare Raspberry Pi Pico C++ SDK

Instructions cheat sheet for Mac OS (see Raspberry Pi docs for more OS examples):

```shell
# From home directory
cd && mkdir pico

# Install pico SDK
git clone -b master https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk/
git submodule update --init

# Add export PICO_SDK_PATH="$HOME/pico/pico-sdk"
nano ~/.bash_profile
source ~/.bash_profile

# Setup build tools
brew install cmake
brew tap ArmMbed/homebrew-formulae
brew install arm-none-eabi-gcc

# In this repo, configure for GCC
mkdir build
cd build

cmake ..
```


## Build the Pico firmware

The MIDI is compiled into a C header, `notes.h`. For example:

```cpp
// GENERATED WITH compile.py

#define NUM_NOTES 2040

// Order is track, pitch, on_at, off_at
static const float* NOTE_TABLE[] = {
  (float[]){ 0, 73, 1.33333, 1.41667 },
  (float[]){ 1, 57, 1.33333, 1.41667 },
  (float[]){ 0, 72, 1.41667, 1.5 },
  (float[]){ 1, 56, 1.41667, 1.5 },
  (float[]){ 0, 71, 1.5, 1.58333 },
  (float[]){ 1, 55, 1.5, 1.58333 },
  (float[]){ 0, 70, 1.58333, 1.66666 },

  // And so on...
```

Additionally, a file for inclusion in a Thumby project is generated as
`track.py`. See [thumby-dev](https://github.com/c-d-lewis/thumby-dev) for more
information.

Build a Pico firmware file:

```shell
cd build

make -j4
```

Finally, copy to the Pico by connecting while 'BOOTSEL' is pressed:

```shell
cp PicoApp.uf2 /Volumes/RPI-RP2/
```

If connected and powered, the Pico will play the tracks chosen on the motors!
