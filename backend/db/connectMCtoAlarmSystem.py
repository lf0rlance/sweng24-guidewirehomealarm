import psycopg2

from db import connectToAlarmSystem
from db import connectToDB


def connectMicroController(microControllerId: int, user_id: int) -> bool:
    conn = connectToDB.connectToDB()
    try:
        system_id = connectToAlarmSystem.getCurrentAlarmSystemID(user_id)
        if system_id is None:
            return False

        cursor = conn.cursor()
        cursor.execute(
            "INSERT into microcontroller(microcontroller_id,alarm_system_id, current_state) VALUES(%s, %s, %s)",
            (microControllerId, system_id, "idle"),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()
