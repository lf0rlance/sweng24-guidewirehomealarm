from db import connectToDB
import psycopg2
import bcrypt

def insertUserInDB(username: str, email: str, alarm_system_id: int | None, password: str) -> bool:
    conn = connectToDB.connectToDB()

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_table(username, email, alarm_system_id, password_hash)
            VALUES(%s, %s, %s, %s)
            """,
            (username, email, alarm_system_id, password_hash)
        )

        conn.commit()
        return True

    except psycopg2.IntegrityError:
        conn.rollback()
        return False

    finally:
        if conn:
            conn.close()
