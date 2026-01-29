import urequests

def send_status(url, payload):
    r = urequests.post(url, json=payload)
    r.close()