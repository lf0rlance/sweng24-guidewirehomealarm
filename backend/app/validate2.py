#required imports
from pydantic import BaseModel, ValidationError, Field, field_validator
from typing import Literal, Annotated
import time
from fastapi import FastAPI

#check version 
#should be 2+
#print(pydantic.__version__)

#did some research and realised that its better to use pydantic module
#it is installed using simple command "pip install pydantic" in your venv
#for example my version 1 was handling error of empty string just using comparison
#if x == ""
#and didnt return any useful information
#also if two string are empty it terminated at the first one, so catching and fixing errors becomes harder
#this module fixes this problem

#has all functionality of previous validation code
#1) check if fields are non empty
#2)check the data type
#3)check for regular expression pattern in device id
#4)check if event is in event list
#5)check that the timestamp is not too far away from current moment


# class ValidateData inherits from basemodel by pydantic (must be defined before use in type hints)
class ValidateData(BaseModel):
    #use regular expression to check whether string follows format esp32_xxxxxx
    #where x are digits
    device_id: Annotated[str, Field(pattern=r"^esp32_\d+$")]
    #event type field can only be one of those in the array, if not -> validation fails
    event_type: Literal["door_open", "door_closed", "alarm_enabled", "alarm_disabled"]
    #count should be of type int and gretater than zero
    count: Annotated[int, Field(gt=0)]
    #time stamp is in unix format, float number
    timestamp: float

    #validation for timestamp
    @field_validator("timestamp")
    def validate_unix_timestamp(cls, value: int) -> int:
        #get current time in unix
        now = int(time.time())
        #account for delay +- 3 min
        max_delay = 180 #seconds
        if(abs(now-value) > max_delay):
            raise ValueError(
                f"timestamp {value} is {abs(now-value)}seconds away from current time stamp.\n Maximum delay allowed is{max_delay}"
            )
        return value


received_count = []

app = FastAPI()


@app.post("/data")
def receive_data(data: ValidateData):
    # Add the count from this request to the array
    received_count.append(data.count)


def validateCount():
    count = 1
    while count < len(received_count):
        if received_count[count - 1] != count:
            print("bad")


# #testing
# try:    
#     data = ValidateData(device_id = "", event_type="door_opesn",count = 0, timestamp=1400)
# except ValidationError as e:
#     print(e)