from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time

from db import connectToDB


@dataclass(frozen=True)
class Membership:
    user_id: int
    alarm_system_id: int
    access_level: str
    can_arm: bool
    can_disarm: bool
    can_view_events: bool
    can_receive_notifications: bool
    can_manage_users: bool


def permissions_for_level(access_level: str) -> Dict[str, bool]:
    level = (access_level or "").strip().lower()
    if level == "owner":
        return {
            "can_arm": True,
            "can_disarm": True,
            "can_view_events": True,
            "can_receive_notifications": True,
            "can_manage_users": True,
        }
    if level in ("trusted_full", "trusted"):
        return {
            "can_arm": True,
            "can_disarm": True,
            "can_view_events": True,
            "can_receive_notifications": True,
            "can_manage_users": False,
        }
    if level in ("child", "trusted_limited"):
        # Limited: can control alarm, but shouldn't see access/sensor notifications/history.
        return {
            "can_arm": True,
            "can_disarm": True,
            "can_view_events": False,
            "can_receive_notifications": False,
            "can_manage_users": False,
        }
    if level in ("arm_only", "arm-only"):
        return {
            "can_arm": True,
            "can_disarm": False,
            "can_view_events": False,
            "can_receive_notifications": False,
            "can_manage_users": False,
        }
    if level in ("viewer", "read_only", "read-only"):
        return {
            "can_arm": False,
            "can_disarm": False,
            "can_view_events": True,
            "can_receive_notifications": True,
            "can_manage_users": False,
        }
    # Default safest: no privileges.
    return {
        "can_arm": False,
        "can_disarm": False,
        "can_view_events": False,
        "can_receive_notifications": False,
        "can_manage_users": False,
    }


def get_membership(user_id: int, alarm_system_id: int) -> Optional[Membership]:
    conn = connectToDB.connectToDB()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_id, alarm_system_id, access_level,
                   can_arm, can_disarm, can_view_events, can_receive_notifications, can_manage_users
            FROM alarm_system_memberships
            WHERE user_id = %s AND alarm_system_id = %s
            """,
            (user_id, alarm_system_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Membership(
            user_id=int(row[0]),
            alarm_system_id=int(row[1]),
            access_level=str(row[2]),
            can_arm=bool(row[3]),
            can_disarm=bool(row[4]),
            can_view_events=bool(row[5]),
            can_receive_notifications=bool(row[6]),
            can_manage_users=bool(row[7]),
        )
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def upsert_membership(user_id: int, alarm_system_id: int, access_level: str) -> bool:
    perms = permissions_for_level(access_level)
    conn = connectToDB.connectToDB()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO alarm_system_memberships (
                user_id, alarm_system_id, access_level,
                can_arm, can_disarm, can_view_events, can_receive_notifications, can_manage_users,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, alarm_system_id) DO UPDATE SET
                access_level = EXCLUDED.access_level,
                can_arm = EXCLUDED.can_arm,
                can_disarm = EXCLUDED.can_disarm,
                can_view_events = EXCLUDED.can_view_events,
                can_receive_notifications = EXCLUDED.can_receive_notifications,
                can_manage_users = EXCLUDED.can_manage_users
            """,
            (
                int(user_id),
                int(alarm_system_id),
                access_level.strip().lower(),
                bool(perms["can_arm"]),
                bool(perms["can_disarm"]),
                bool(perms["can_view_events"]),
                bool(perms["can_receive_notifications"]),
                bool(perms["can_manage_users"]),
                float(time.time()),
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"upsert_membership failed: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def remove_membership(user_id: int, alarm_system_id: int) -> bool:
    conn = connectToDB.connectToDB()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM alarm_system_memberships WHERE user_id = %s AND alarm_system_id = %s",
            (int(user_id), int(alarm_system_id)),
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"remove_membership failed: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_members(alarm_system_id: int) -> List[Dict]:
    conn = connectToDB.connectToDB()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.user_id, u.username, u.email,
                   m.access_level,
                   m.can_arm, m.can_disarm, m.can_view_events, m.can_receive_notifications, m.can_manage_users
            FROM alarm_system_memberships m
            JOIN user_table u ON u.id = m.user_id
            WHERE m.alarm_system_id = %s
            ORDER BY m.can_manage_users DESC, m.access_level ASC, u.username ASC
            """,
            (int(alarm_system_id),),
        )
        rows = cur.fetchall()
        out: List[Dict] = []
        for r in rows:
            out.append(
                {
                    "user_id": int(r[0]),
                    "username": r[1],
                    "email": r[2],
                    "access_level": r[3],
                    "can_arm": bool(r[4]),
                    "can_disarm": bool(r[5]),
                    "can_view_events": bool(r[6]),
                    "can_receive_notifications": bool(r[7]),
                    "can_manage_users": bool(r[8]),
                }
            )
        return out
    except Exception as e:
        print(f"list_members failed: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

