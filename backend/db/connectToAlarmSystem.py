import re
import connectToDB
import psycopg2
import addAvailableSystems


def getCurrentAlarmSystemID(username: str) -> str | None:
    conn = connectToDB.connectToDB()
    cursor = conn.cursor()

    cursor.execute("SELECT alarm_system_id FROM user_table WHERE username = %s", (username,))
    row = cursor.fetchone()
    currentAlarmSystemID = row[0] if row else None

    conn.close()

    return currentAlarmSystemID


def get_alarm_system_id_by_user_id(user_id: int) -> int | None:
    """Return alarm_system_id for the given user (by user_table.id). None if not paired or not found."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT alarm_system_id FROM user_table WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_alarm_system_id_by_device_id(device_id: str) -> int | None:
    """
    Return alarm_system_id for the device (e.g. esp32_123456 -> lookup microcontroller_id 123456).
    None if device not registered or not found.
    """
    match = re.match(r"^esp32_(\d+)$", (device_id or "").strip())
    if not match:
        return None
    mc_id = int(match.group(1))
    conn = connectToDB.connectToDB()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT alarm_system_id FROM microcontroller WHERE microcontroller_id = %s",
            (mc_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


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
if __name__ == "__main__":
    connectUserToSystem("test2")