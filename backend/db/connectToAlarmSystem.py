import bcrypt

from db import connectToDB


def getCurrentAlarmSystemID(user_id: int) -> int | None:
    conn = connectToDB.connectToDB()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT alarm_system_id FROM user_table WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return row[0]
    finally:
        conn.close()


def connectUserToSystem(user_id: int, system_password: str) -> bool:
    """
    Pair the authenticated user with an existing unpaired alarm system by password.
    """
    conn = connectToDB.connectToDB()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT alarm_system_id FROM user_table WHERE id = %s", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return False

        current_system_id = user_row[0]
        if current_system_id is not None:
            return False

        cursor.execute(
            """
            SELECT alarm_system_id, system_password_hash
            FROM alarm_system_table
            WHERE paired = FALSE
            """
        )
        candidates = cursor.fetchall()

        matched_system_id = None
        for alarm_system_id, password_hash in candidates:
            if bcrypt.checkpw(system_password.encode(), password_hash.encode()):
                matched_system_id = alarm_system_id
                break

        if matched_system_id is None:
            return False

        cursor.execute(
            """
            UPDATE user_table
            SET alarm_system_id = %s
            WHERE id = %s
            """,
            (matched_system_id, user_id),
        )
        cursor.execute(
            "UPDATE alarm_system_table SET paired = TRUE WHERE alarm_system_id = %s",
            (matched_system_id,),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()
