# WiFi Mode: "AP" for Access Point (ESP32 creates hotspot) or "STA" for Station (ESP32 connects to existing WiFi)
WIFI_MODE = "AP"

# Access Point settings (when ESP32 creates its own WiFi)
AP_SSID = "ESP32_HomeAlarm"
AP_PASSWORD = "Group24"  # Must be at least 8 characters

# Station mode settings (when ESP32 connects to existing WiFi)
WIFI_SSID = "wifi_name"
WIFI_PASSWORD = "wifi_pass"

# Backend configuration
# For AP mode: laptop connects to ESP32 WiFi and gets IP 192.168.4.2
# ESP32 sends events to the laptop
# should add security here, maybe use esp32 auth token that backend can validate 
BACKEND_URL = "http://192.168.4.2:5000/data"