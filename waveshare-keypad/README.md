# waveshare-3.5in-lcd

Micropython scripts that use a Waveshare 3.5in LCD for Pico kit to implement
a visual version of the `keypad-base` project.

## Development

Development is easily done in Thonny when a Pico with Micropython is connected,
though code editing is not so easy.

### Copy in Windows

To avoid clicking lots of GUI options, it is possible to copy files directly.

1. Open PowerShell and navigate to `cd \\wsl$\Ubuntu`
2. Navigate to the project directory.
3. Check devices with `mpremote devs`

Then copy files:

```
fs cp .\main.py :.
```
