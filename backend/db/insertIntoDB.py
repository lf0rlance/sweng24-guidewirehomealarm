import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

#tuple size has to be at least length = 4
def insertUserInDB(userInfoTuple: tuple) -> None:
    #establish connection
    conn = None
    try:
        #load env variables from backend
        env_path = Path(__file__).resolve().parents[1] / ".env.example"
        load_dotenv(env_path)
        password = os.getenv("DATABASE_PASSWORD")
        host = os.getenv("DATABASE_HOST")

        conn = psycopg2.connect(
            database = "alarm_system",
            user = "postgres",
            password = password,
            host = host,
            port = "5432"
        )

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
    
testTuple = ("test5", "test5@random.ie", None, "xyz")
insertUserInDB(testTuple)
