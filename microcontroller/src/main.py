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
def toggle():
    while True:
        led.value(1)
        time.sleep(1)
        led.value(0)
        time.sleep(1)

events = EventManager(device_id="esp32_001")
events.do("led_toggle", toggle)

while True:
    events.check_all()
    time.sleep(0.1)  # check 10 times per second
