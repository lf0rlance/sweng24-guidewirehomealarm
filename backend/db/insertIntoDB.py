import connectToDB
import psycopg2
import bcrypt

#tuple size has to be at least length = 4
def insertUserInDB(userInfoTuple: tuple) -> None:
    #establish connection
    conn = connectToDB.connectToDB()
    password = userInfoTuple[3]
    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    try:
        #create cursor
        cursor = conn.cursor()

        cursor.execute("INSERT into user_table(username, email, alarm_system_id, password_hash) VALUES(%s, %s, %s, %s)", userInfoTuple)

        print("The insertion was successful!")

        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        return False  # username or email already exists
    finally:
        if conn:
            conn.close()