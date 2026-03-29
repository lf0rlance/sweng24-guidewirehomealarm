"""Admin-only DB helpers: list homes (no address), add home, list users per home."""
import psycopg2
from typing import List, Optional
from db import connectToDB
from db.addAvailableSystems import create_home_with_device
from db.device_last_seen import get_all_last_seen, get_offline_devices
from db.sensor_labels import get_sensor_labels


def list_homes() -> List[dict]:
    """
    List all alarm systems with their microcontroller device_id, last_seen, sensor labels, user count.
    No home address or location is ever stored or returned.
    """
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT a.alarm_system_id, COALESCE(a.name, ''), m.microcontroller_id, m.current_state
                FROM alarm_system_table a
                LEFT JOIN microcontroller m ON m.alarm_system_id = a.alarm_system_id
                ORDER BY a.alarm_system_id
                """
            )
            rows = cur.fetchall()
            has_name = True
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            cur.execute(
                """
                SELECT a.alarm_system_id, m.microcontroller_id, m.current_state
                FROM alarm_system_table a
                LEFT JOIN microcontroller m ON m.alarm_system_id = a.alarm_system_id
                ORDER BY a.alarm_system_id
                """
            )
            rows = cur.fetchall()
            has_name = False
        last_seen_map = {(mc_id, aid): ts for mc_id, aid, ts in get_all_last_seen()}
        offline_set = {(mc_id, aid) for mc_id, aid, _ in get_offline_devices(300)}
        cur.execute(
            """
            SELECT alarm_system_id, COUNT(*) FROM user_table
            WHERE alarm_system_id IS NOT NULL
            GROUP BY alarm_system_id
            """
        )
        user_counts = dict(cur.fetchall())
        out = []
        for row in rows:
            if has_name:
                aid, name, mc_id, state = row
                name = (name or "").strip()
            else:
                aid, mc_id, state = row
                name = ""
            device_id = f"esp32_{mc_id}" if mc_id is not None else None
            last_ts = last_seen_map.get((mc_id, aid)) if mc_id else None
            out.append({
                "alarm_system_id": aid,
                "name": (name or "").strip(),
                "microcontroller_id": mc_id,
                "device_id": device_id,
                "current_state": state,
                "last_seen": last_ts,
                "offline": (mc_id, aid) in offline_set if mc_id else False,
                "sensor_labels": get_sensor_labels(aid) if aid else [],
                "user_count": user_counts.get(aid, 0),
            })
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_home_name(alarm_system_id: int, name: str) -> bool:
    """Set display name for an alarm system. No address stored."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE alarm_system_table SET name = %s WHERE alarm_system_id = %s",
            (name.strip()[:120] if name else None, alarm_system_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"update_home_name failed: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_home(alarm_system_id: int) -> tuple:
    """Unlink users, then delete dependent rows in order, then the alarm system. Returns (success, error_message)."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE user_table SET alarm_system_id = NULL WHERE alarm_system_id = %s",
            (alarm_system_id,),
        )
        cur.execute(
            "DELETE FROM device_last_seen WHERE microcontroller_id IN (SELECT microcontroller_id FROM microcontroller WHERE alarm_system_id = %s)",
            (alarm_system_id,),
        )
        cur.execute("DELETE FROM microcontroller WHERE alarm_system_id = %s", (alarm_system_id,))
        cur.execute("DELETE FROM sensor_labels WHERE alarm_system_id = %s", (alarm_system_id,))
        for sql in [
            "DELETE FROM fcm_tokens WHERE alarm_system_id = %s",
            "DELETE FROM sensor_events WHERE alarm_system_id = %s",
        ]:
            try:
                cur.execute(sql, (alarm_system_id,))
            except Exception:
                pass
        cur.execute("DELETE FROM alarm_system_table WHERE alarm_system_id = %s", (alarm_system_id,))
        conn.commit()
        return (True, None)
    except Exception as e:
        conn.rollback()
        err_msg = str(e)
        print(f"delete_home failed: {err_msg}")
        return (False, err_msg)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def add_home(microcontroller_id: Optional[int] = None) -> Optional[dict]:
    """
    Create one home (alarm_system + microcontroller). Returns dict with alarm_system_id, device_id, etc.
    Raises ValueError if microcontroller_id is invalid or already used.
    """
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        aid, mc_id, device_id = create_home_with_device(cur, microcontroller_id=microcontroller_id)
        conn.commit()
        return {
            "alarm_system_id": aid,
            "microcontroller_id": mc_id,
            "device_id": device_id,
        }
    except ValueError:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"add_home failed: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_users_for_home(alarm_system_id: int) -> List[dict]:
    """List users linked to this home. No address; only id, username, email, phone for contact."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, username, email, COALESCE(phone, '') as phone, role,
                       COALESCE(home_role, 'owner') as home_role
                FROM user_table
                WHERE alarm_system_id = %s
                ORDER BY id
                """,
                (alarm_system_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "username": r[1],
                    "email": r[2],
                    "phone": r[3],
                    "role": r[4],
                    "home_role": str(r[5]).strip().lower() if len(r) > 5 and r[5] else "owner",
                }
                for r in rows
            ]
        except Exception:
            conn.rollback()
            cur.execute(
                """
                SELECT id, username, email, COALESCE(phone, '') as phone, role
                FROM user_table
                WHERE alarm_system_id = %s
                ORDER BY id
                """,
                (alarm_system_id,),
            )
            return [
                {
                    "id": r[0],
                    "username": r[1],
                    "email": r[2],
                    "phone": r[3],
                    "role": r[4],
                    "home_role": "owner",
                }
                for r in cur.fetchall()
            ]
    finally:
        try:
            conn.close()
        except Exception:
            pass

