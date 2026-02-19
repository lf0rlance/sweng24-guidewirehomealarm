import urequests

def send_status(url, payload):
    try:
        r = urequests.post(url, json=payload, timeout=5)
        print("Response Status:", r.status_code) 
        print("Response Text:", r.text)
        r.close()
    except Exception as e:
        raise e