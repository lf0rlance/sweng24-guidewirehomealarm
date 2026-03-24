# WiFi Mode: "AP" for Access Point (ESP32 creates hotspot) or "STA" for Station (ESP32 connects to existing WiFi)
WIFI_MODE = "STA"

# Access Point settings 
AP_SSID = "ESP32_HomeAlarm"
AP_PASSWORD = "Group24"  # Must be at least 8 characters

# Station mode settings 
WIFI_SSID = "INSERT WIFI SSID"
WIFI_PASSWORD = "WORDPASS321"

# Backend configuration
#Set URL to http:// (INSERT IP here):(INSERT PORT HERE)/api/events
BACKEND_URL = "http://172.20.10.5:5000/api/events"