import connectToDB
import psycopg2

#tuple size has to be at least length = 4
def insertUserInDB(userInfoTuple: tuple) -> None:
    #establish connection
    conn = connectToDB.connectToDB()
    try:
        #create cursor
        cursor = conn.cursor()

        #p.s well have to think where the password string will be converted to hash
        cursor.execute("INSERT into user_table(username, email, alarm_system_id, password_hash) VALUES(%s, %s, %s, %s)", userInfoTuple)

        print("The insertion was successful!")

        conn.commit()
    except:
        print("The insertion failed")
    finally:
        if conn:
            conn.close()