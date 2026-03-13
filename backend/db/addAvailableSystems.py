from db import connectToDB
#hashing
import bcrypt
import psycopg2
#real random
import secrets
import string

def generate_random_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_alarm_system(cur) -> tuple[int, str]:
    password = generate_random_password(12)
    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    cur.execute(
        """
        INSERT INTO alarm_system_table (
            system_password_hash,
            armed,
            paired
        )
        VALUES (%s, FALSE, FALSE)
        RETURNING alarm_system_id
        """,
        (password_hash,)
    )

    alarm_system_id = cur.fetchone()[0]
    return alarm_system_id, password


#testing


# def addAlarmSystems(numberOfSystems: int) -> None:
#     conn = connectToDB.connectToDB()
#     try:
#         cursor = conn.cursor()

#         for _ in range(numberOfSystems):
#             system_id, password = create_alarm_system(cursor)
#             print(f"Created alarm system {system_id} with password {password}")

#         conn.commit()

#     except Exception:
#         conn.rollback()
#         raise

#     finally:
#         conn.close()


# addAlarmSystems(10)