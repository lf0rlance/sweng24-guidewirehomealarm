import machine
import time
import wifi
import config
from events import EventManager

# wifi setup
if config.WIFI_MODE == "AP":
    esp_ip = wifi.create_ap(config.AP_SSID, config.AP_PASSWORD)
    print("ESP32 IP: " + esp_ip)
else:
    if wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
        print("WiFi connected successfully")
    else:
        print("WiFi connection failed")

led = machine.Pin(2, machine.Pin.OUT)
reed = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
events = EventManager(device_id="esp32_001")

# track reed switch state and debounce
reed_state = reed.value()
last_reed_change = time.ticks_ms()
DEBOUNCE_MS = 10

def check_toggle():
    global reed_state, last_reed_change
    
    current_time = time.ticks_ms()
    current_reed = reed.value()
    
    # Debounce: only toggle if reed state changed and debounce period passed
    if current_reed != reed_state and current_time - last_reed_change >= DEBOUNCE_MS:
        reed_state = current_reed
        last_reed_change = current_time
        
        # Toggle LED when reed switch changes (magnetic contact detected)d
        led.value(not reed_state)
        return {"state": "on" if led.value() else "off"}
    
    return False

events.on("led_toggle", check_toggle)

while True:
    events.check_all()
    time.sleep(0.1)  # check 10 times per second
