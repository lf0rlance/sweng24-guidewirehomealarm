import connectToDB
import psycopg2

#in development
###############################################################################################
def getUser(username: str, password: str) -> tuple:
    conn = connectToDB.connectToDB()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM user_table WHERE username = %s", (username,))

    stored_hash = cur.fetchone()[0]

    if bcrypt.checkpw(entered_password.encode(), stored_hash.encode()):
        cursor.execute("SELECT alarm_system_id FROM user_table WHERE username = %s", (username,))


    else:
        pass
#################################################################################################