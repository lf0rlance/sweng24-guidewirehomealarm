import machine
import time
import wifi
import config
from events import EventManager

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

reed_state = reed.value()
last_reed_change = time.ticks_ms()
DEBOUNCE_MS = 500  # was 10, now 500ms

def check_sensors():
    global reed_state, last_reed_change
    now = time.ticks_ms()
    cur = reed.value()
    if cur == reed_state:
        return  # no change
    if time.ticks_diff(now, last_reed_change) < DEBOUNCE_MS:
        return  # too soon, ignore bounce
    reed_state = cur
    last_reed_change = now
    if cur == 1:
        led.value(1)
        events.send("door_open")
    else:
        led.value(0)
        events.send("door_closed")

while True:
    check_sensors()
    time.sleep(0.1)