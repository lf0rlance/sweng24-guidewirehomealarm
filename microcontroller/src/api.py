import urequests

def send_status(url, payload):
    try:
        r = urequests.post(url, json=payload, timeout=2)
        r.close()
    except Exception as e:
        raise e