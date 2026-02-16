import unittest
from app.validate2 import ValidateData, receive_data, validateCount

data = ValidateData(device_id = "", event_type="door_opesn",count = 0, timestamp=1400)

try:    
    data = ValidateData(device_id = "", event_type="door_opesn",count = 0, timestamp=1400)
except ValidationError as e:
    print(e)