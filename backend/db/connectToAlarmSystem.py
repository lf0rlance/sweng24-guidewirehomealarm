import connectToDB
import psycopg2
import addAvailableSystems

def getCurrentAlarmSystemID(username: str) -> str | None:
    conn = connectToDB.connectToDB()
    cursor = conn.cursor()

    cursor.execute("SELECT alarm_system_id FROM user_table WHERE username = %s", (username,))
    currentAlarmSystemID = cursor.fetchone()[0]
    
    conn.close()
    
    return currentAlarmSystemID


def connectUserToSystem(username: str) -> None:
    systemId = getCurrentAlarmSystemID(username)

    if(systemId == None):
        print("You have to pair your account with alarm system")
        
        conn = connectToDB.connectToDB()

        cursor = conn.cursor()

        systemId, password = addAvailableSystems.create_alarm_system(cursor)
        print(f"Created alarm system {systemId} with password {password}")

        cursor.execute(
        """
        UPDATE user_table
        SET alarm_system_id = %s
        WHERE username = %s
        """,
        (systemId, username)
        )

        cursor.execute("UPDATE alarm_system_table SET paired = %s WHERE alarm_system_id = %s", ("T", systemId))
        conn.commit()

    else:
        print(f"You are paired already to system {systemId}")

#testing
connectUserToSystem("test2")