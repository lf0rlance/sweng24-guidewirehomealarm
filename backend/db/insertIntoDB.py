import bcrypt
import psycopg2

from db import connectToDB


def insertUserInDB(
    username: str,
    email: str,
    alarm_system_id: int | None,
    password: str,
) -> bool:
    conn = connectToDB.connectToDB()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT into user_table(username, email, alarm_system_id, password_hash) VALUES(%s, %s, %s, %s)",
            (username, email, alarm_system_id, password_hash),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()
