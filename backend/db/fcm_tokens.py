"""Persist and load FCM tokens per alarm system so push works after backend restart."""
from typing import List

from db import connectToDB


def save_fcm_token(alarm_system_id: int, token: str) -> bool:
    """Register or update a device token for an alarm system. Returns True on success."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM fcm_tokens WHERE token = %s", (token,))
        cur.execute(
            "INSERT INTO fcm_tokens (token, alarm_system_id) VALUES (%s, %s)",
            (token, alarm_system_id),
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"FCM token save failed (table may not exist): {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_fcm_tokens(alarm_system_id: int) -> List[str]:
    """Return all FCM tokens registered for this alarm system."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT token FROM fcm_tokens WHERE alarm_system_id = %s", (alarm_system_id,))
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"FCM token load failed (table may not exist): {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass
