import connectToDB
import psycopg2
import getModeOfSystem

#function to set the mode 
def setMode(alarm_system_id: int, value: bool) -> bool:
    conn = connectToDB.connectToDB()

    cursor = conn.cursor()
    currentMode = getModeOfSystem.getModeBySysId(alarm_system_id)
    
    if(currentMode != value):
        try:
            cursor.execute("UPDATE alarm_system_table SET armed = %s WHERE alarm_system_id = %s;", (value, alarm_system_id))
            return True
        except:
            raise("Couldnt make an update")
            return False
    else:
        raise(f"The value is already set to {value}")
        return False