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
        print("WiFi connected successfully" )
    else:
        print("WiFi connection failed")


led = machine.Pin(2, machine.Pin.OUT)
reed = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
events = EventManager(device_id="esp32_001")

# Reed: 0 = closed (magnet near), 1 = open (magnet away). Debounce state.
reed_state = reed.value()
last_reed_change = time.ticks_ms()
DEBOUNCE_MS = 10

def check_door_open():
    """Send door_open when reed goes to open (1)."""
    global reed_state, last_reed_change
    now = time.ticks_ms()
    cur = reed.value()
    if cur != reed_state and now - last_reed_change >= DEBOUNCE_MS and cur == 1:
        reed_state = cur
        last_reed_change = now
        led.value(1)
        return True
    return False

def check_door_closed():
    """Send door_closed when reed goes to closed (0)."""
    global reed_state, last_reed_change
    now = time.ticks_ms()
    cur = reed.value()
    if cur != reed_state and now - last_reed_change >= DEBOUNCE_MS and cur == 0:
        reed_state = cur
        last_reed_change = now
        led.value(0)
        return True
    return False

events.on("door_open", check_door_open)
events.on("door_closed", check_door_closed)

while True:
    events.check_all()
    time.sleep(0.1)  # check 10 times per second
