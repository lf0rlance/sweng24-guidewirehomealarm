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
events = EventManager(device_id="esp32_001")

# ex for now to test
led_state = [0]
last_toggle_time = [0]

def check_toggle():
    current_time = time.time()
    if current_time - last_toggle_time[0] >= 1:
        last_toggle_time[0] = current_time
        led_state[0] = 1 - led_state[0]
        led.value(led_state[0])
        return {"state": "on" if led_state[0] else "off"}
    return False

events.on("led_toggle", check_toggle)

while True:
    events.check_all()
    time.sleep(0.1)  # check 10 times per second
