#!/bin/bash

set -eu

MIDI_PATH=$1
TRACK_LIST=$2
RPI_PATH=$3  # e.g /media/chris/RPI-RP2/

# Compile MIDI
python3 compile.py "$MIDI_PATH" "$TRACK_LIST"

# Compile binary
cd build/ && make && cd -

# Wait for board to connect
echo ""
echo "Waiting for Pico to connect..."
until [ -d $RPI_PATH ]
do
  sleep 1
done

# Copy to Pico
echo ""
echo "Copying to Pico..."
cp build/PicoApp.uf2 $RPI_PATH
echo "Done!"
echo ""
