"""Persist and load FCM tokens for push notifications.

Historically this stored one token per alarm system. We now also store `user_id`
so we can suppress notifications for limited-access members (e.g. children).
"""
from typing import List, Optional

from db import connectToDB


def save_fcm_token(alarm_system_id: int, token: str, user_id: Optional[int] = None) -> bool:
    """Register or update a device token. Returns True on success."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM fcm_tokens WHERE token = %s", (token,))
        cur.execute(
            "INSERT INTO fcm_tokens (token, alarm_system_id, user_id) VALUES (%s, %s, %s)",
            (token, alarm_system_id, int(user_id) if user_id is not None else None),
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


def get_fcm_tokens_for_users(alarm_system_id: int, user_ids: List[int]) -> List[str]:
    """Return tokens for specific users in this alarm system."""
    if not user_ids:
        return []
    conn = connectToDB.connectToDB()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT token
            FROM fcm_tokens
            WHERE alarm_system_id = %s AND user_id = ANY(%s)
            """,
            (int(alarm_system_id), user_ids),
        )
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"FCM token load failed: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass
