from __future__ import annotations

import secrets
import time
from typing import Optional, Tuple

from db import connectToDB


def _generate_code(length: int = 8) -> str:
    # Avoid ambiguous chars (0/O, 1/I) for humans reading codes.
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(max(6, int(length))))


def create_one_time_disarm_code(
    alarm_system_id: int,
    created_by_user_id: int,
    ttl_seconds: int = 600,
) -> Optional[str]:
    """Create a single-use disarm code for this home/system."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        code = _generate_code(8)
        now = float(time.time())
        expires_at = now + max(60, int(ttl_seconds))
        cur.execute(
            """
            INSERT INTO one_time_disarm_codes (
              alarm_system_id, code, created_by_user_id, created_at, expires_at, used_at, used_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, NULL, NULL)
            """,
            (int(alarm_system_id), code, int(created_by_user_id), now, float(expires_at)),
        )
        conn.commit()
        return code
    except Exception as e:
        conn.rollback()
        print(f"create_one_time_disarm_code failed: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def consume_one_time_disarm_code(
    alarm_system_id: int,
    code: str,
    used_by_user_id: int,
) -> Tuple[bool, str]:
    """
    Mark code as used if valid (single-use + not expired).
    Returns (ok, error_message).
    """
    code_norm = (code or "").strip().upper()
    if not code_norm:
        return (False, "Missing code")
    conn = connectToDB.connectToDB()
    if conn is None:
        return (False, "Database unavailable")
    try:
        cur = conn.cursor()
        now = float(time.time())
        # Lock row so two requests can't use same code.
        cur.execute(
            """
            SELECT expires_at, used_at
            FROM one_time_disarm_codes
            WHERE alarm_system_id = %s AND code = %s
            FOR UPDATE
            """,
            (int(alarm_system_id), code_norm),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return (False, "Invalid code")
        expires_at, used_at = row
        if used_at is not None:
            conn.rollback()
            return (False, "Code already used")
        if expires_at is not None and float(expires_at) < now:
            conn.rollback()
            return (False, "Code expired")
        cur.execute(
            """
            UPDATE one_time_disarm_codes
            SET used_at = %s, used_by_user_id = %s
            WHERE alarm_system_id = %s AND code = %s AND used_at IS NULL
            """,
            (now, int(used_by_user_id), int(alarm_system_id), code_norm),
        )
        conn.commit()
        if cur.rowcount <= 0:
            return (False, "Code already used")
        return (True, "")
    except Exception as e:
        conn.rollback()
        print(f"consume_one_time_disarm_code failed: {e}")
        return (False, "Server error")
    finally:
        try:
            conn.close()
        except Exception:
            pass

