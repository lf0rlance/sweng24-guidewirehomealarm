import psycopg2
import connectToDB
import connectToAlarmSystem

def connectMicroController(microControllerId: int , username: str) -> bool:
    conn = connectToDB.connectToDB()
    systemId = connectToAlarmSystem.getCurrentAlarmSystemID(username)

    if(systemId != None):
        try:   
            cursor = conn.cursor()
            

            cursor.execute("INSERT into microcontroller(microcontroller_id,alarm_system_id, current_state) VALUES(%s, %s, %s)", (microControllerId, systemId, "idle"))
            conn.commit()
            print("Microcontroller is added to system")
            return True
        except:
            #undoes all the changes
            conn.rollback()
            print("Couldnt connect microcontroller")
        

            return False
    else:
        print("The system id is none")
        return False

connectMicroController("666", "luhinm")