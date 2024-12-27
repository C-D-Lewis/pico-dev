import os

# Wi-Fi SSID
WIFI_SSID = os.getenv('WIFI_SSID')
# Wi-Fi password
WIFI_PASSWORD = os.getenv('WIFI_PASSWORD')

# The current screensaver
SCREENSAVER = os.getenv('SCREENSAVER')

# If WiFi is not configured, don't do anything NTP or internet related
IS_WIFI_ENABLED = WIFI_SSID is not None and WIFI_PASSWORD is not None
