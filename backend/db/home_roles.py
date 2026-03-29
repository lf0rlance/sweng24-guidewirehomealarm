"""Per-home roles: owner, spouse, child, trusted (separate from platform admin/user role)."""
from typing import List, Optional, Set

from db import connectToDB

HOME_ROLES: Set[str] = {"owner", "spouse", "child", "trusted"}


def get_home_role(user_id: int) -> Optional[str]:
    """Return home_role for this user, or None if not linked to a home."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT alarm_system_id, COALESCE(home_role, 'owner')
            FROM user_table WHERE id = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if not row or row[0] is None:
            return None
        return str(row[1]).strip().lower() if row[1] else "owner"
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def count_users_in_home(alarm_system_id: int) -> int:
    conn = connectToDB.connectToDB()
    if conn is None:
        return 0
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM user_table WHERE alarm_system_id = %s",
            (alarm_system_id,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


def home_has_owner(alarm_system_id: int) -> bool:
    conn = connectToDB.connectToDB()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM user_table
            WHERE alarm_system_id = %s AND COALESCE(home_role, 'owner') = 'owner'
            LIMIT 1
            """,
            (alarm_system_id,),
        )
        return cur.fetchone() is not None
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def user_ids_guardians(alarm_system_id: int) -> List[int]:
    """Users who should be notified of child/trusted arm-disarm actions (owner + spouse)."""
    conn = connectToDB.connectToDB()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id FROM user_table
            WHERE alarm_system_id = %s
              AND COALESCE(home_role, 'owner') IN ('owner', 'spouse')
            """,
            (alarm_system_id,),
        )
        return [int(r[0]) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def user_ids_owners_only(alarm_system_id: int) -> List[int]:
    conn = connectToDB.connectToDB()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id FROM user_table
            WHERE alarm_system_id = %s AND COALESCE(home_role, 'owner') = 'owner'
            """,
            (alarm_system_id,),
        )
        return [int(r[0]) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_username(user_id: int) -> str:
    conn = connectToDB.connectToDB()
    if conn is None:
        return "User"
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(username, email, '') FROM user_table WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if row and row[0]:
            return str(row[0])[:80]
        return "User"
    except Exception:
        return "User"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def can_view_history(home_role: Optional[str]) -> bool:
    if home_role is None:
        return True
    return home_role not in ("child", "trusted")
