#!/bin/bash

set -e

MIDI_PATH=$1
TRACK_LIST=$2

# Compile MIDI
python3 compile.py "$MIDI_PATH" "$TRACK_LIST"

# Compile binary
cd build/ && make && cd -

# Wait for board to connect
echo ""
echo "Waiting for Pico to connect..."
until [ -d /Volumes/RPI-RP2/ ]
do
  sleep 1
done

# Copy to Pico
echo ""
echo "Copying to Pico..."
cp build/PicoApp.uf2 /Volumes/RPI-RP2/
echo "Done!"
echo ""
