# WiFi Mode: "AP" for Access Point (ESP32 creates hotspot) or "STA" for Station (ESP32 connects to existing WiFi)
WIFI_MODE = "STA"

# Access Point settings 
AP_SSID = "ESP32_HomeAlarm"
AP_PASSWORD = "Group24"  # Must be at least 8 characters

# Station mode settings 
WIFI_SSID = "Pixel_2602"
WIFI_PASSWORD = "00000000"

# Backend: Pi (or dev PC) on your LAN — same URL the phone uses, port 8000 if using Docker.
# Use /api/events/ingest with X-ESP32-Secret (see backend ESP32_INGEST_SECRET in .env).
BACKEND_URL = "http://10.40.244.187:8000/api/events/ingest"
# Must match backend/.env ESP32_INGEST_SECRET (set a long random string on the Pi).
ESP32_INGEST_SECRET = "whatever"

# Unique per physical board. Must match microcontroller_id in the DB: esp32_001 -> id 1, esp32_002 -> id 2, etc.
# Flash different config.py on each ESP32 (or edit this line before uploading).
DEVICE_ID = "esp32_001"

# Reed / magnetic sensors: GPIO number, pull-up, active HIGH when open (adjust if your wiring differs).
REED1_PIN = 4   # D4 — first sensor
REED2_PIN = 14  # D14 — second sensor (set to None to disable)