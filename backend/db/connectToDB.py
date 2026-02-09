import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

def connectToDB():
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
    except:
        raise("Connection unsuccessful")
    finally:
        return conn
        