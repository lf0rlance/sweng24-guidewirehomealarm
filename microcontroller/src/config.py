# WiFi Mode: "AP" for Access Point (ESP32 creates hotspot) or "STA" for Station (ESP32 connects to existing WiFi)
WIFI_MODE = "STA"

# Access Point settings (when ESP32 creates its own WiFi)
AP_SSID = "ESP32_HomeAlarm"
AP_PASSWORD = "Group24"  # Must be at least 8 characters

# Station mode settings (when ESP32 connects to existing WiFi)
WIFI_SSID = "Matthew’s bluetooth wheelchair"
WIFI_PASSWORD = "bruhface"

# Backend configuration
# For STA mode: ESP32 connects to mobile hotspot, backend runs on laptop's IP on hotspot network
BACKEND_URL = "http://172.20.10.5:5000/api/events"