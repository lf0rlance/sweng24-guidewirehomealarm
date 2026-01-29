import time
import api
import config

class EventManager:
    def __init__(self, device_id="esp32_001"):
        self.device_id = device_id
        self.event_count = 0
        self.handlers = []
    
    def send(self, event_type, **kwargs):
        self.event_count += 1
        
        payload = {
            "event_type": event_type,
            "device_id": self.device_id,
            "count": self.event_count,
            "timestamp": time.time()
        }
        # kwargs passes event data w/o defining specific event parameters
        payload.update(kwargs)
        
        try:
            api.send_status(config.BACKEND_URL, payload)
            print("Event " + str(self.event_count) + " sent: " + event_type)
            return True
        except Exception as e:
            print("Failed to send event: " + str(e))
            return False
    
    def do(self, event_type, action, **kwargs):
        result = action() if callable(action) else None
        
        if isinstance(result, dict):
            kwargs.update(result)
        
        return self.send(event_type, **kwargs)
    
    # This can be used once we are waiting for events to be triggered
    # register once
    #   motion = machine.Pin(14, machine.Pin.IN)
    #   events.on("motion_detected", lambda: motion.value() == 1)
    # def on(self, event_type, trigger_func, handler_func=None):
    #     """Register a handler that checks trigger and sends event when activated
        
    #     Args:
    #         event_type: Name of the event to send
    #         trigger_func: Function that returns True when triggered, or dict with data
    #         handler_func: Optional function to execute when triggered
    #     """
    #     self.handlers.append({
    #         "event_type": event_type,
    #         "trigger": trigger_func,
    #         "handler": handler_func
    #     })
    


    # def check_temp():
    # temp = sensor.read()
    # if temp > 30:
    #     return {"temp": temp, "warning": True}
    # return False

    # events.on("high_temp", check_temp)

    # def check_all(self):
    #     """Check all registered handlers and send events for triggered ones"""
    #     for h in self.handlers:
    #         result = h["trigger"]()
            
    #         if result:
    #             # Execute handler if provided
    #             if h["handler"]:
    #                 h["handler"]()
                
    #             # Prepare event data
    #             data = result if isinstance(result, dict) else {}
                
    #             # Send event
    #             self.send(h["event_type"], **data)
        
