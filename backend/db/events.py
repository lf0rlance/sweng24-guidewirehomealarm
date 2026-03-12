from typing import List, Dict, Optional

import psycopg2

from db import connectToDB


def save_event(event_dict: Dict, alarm_system_id: Optional[int], was_armed: bool) -> None:
    """
    Persist a single sensor event to the database.

    event_dict is the validated payload from ValidateData plus a server-side timestamp.
    """
    if alarm_system_id is None:
        # If we somehow don't know which alarm system this belongs to, skip persisting.
        return

    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_events (
                id BIGSERIAL PRIMARY KEY,
                alarm_system_id INT NOT NULL REFERENCES alarm_system_table (alarm_system_id) ON DELETE CASCADE,
                device_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                count INT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL,
                was_armed BOOLEAN NOT NULL
            );
            """,
        )
        cur.execute(
            """
            INSERT INTO sensor_events (
                alarm_system_id, device_id, event_type, count, timestamp, was_armed
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                alarm_system_id,
                event_dict.get("device_id"),
                event_dict.get("event_type"),
                int(event_dict.get("count") or 0),
                float(event_dict.get("timestamp") or 0.0),
                bool(was_armed),
            ),
        )
        conn.commit()
    except Exception as e:
        # For now just log; API should still succeed so the in-memory/event-stream behaviour is unchanged.
        print(f"Event persist failed: {e}")
        conn.rollback()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_events_for_system(alarm_system_id: int, armed_only: bool = True, limit: int = 500) -> List[Dict]:
    """
    Load historical events for a given alarm system, newest first.

    If armed_only is True, only return events that were recorded while the system was armed
    (matches previous in-memory behaviour).
    """
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_events (
                id BIGSERIAL PRIMARY KEY,
                alarm_system_id INT NOT NULL REFERENCES alarm_system_table (alarm_system_id) ON DELETE CASCADE,
                device_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                count INT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL,
                was_armed BOOLEAN NOT NULL
            );
            """,
        )
        if armed_only:
            cur.execute(
                """
                SELECT device_id, event_type, count, timestamp
                FROM sensor_events
                WHERE alarm_system_id = %s AND was_armed = TRUE
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (alarm_system_id, limit),
            )
        else:
            cur.execute(
                """
                SELECT device_id, event_type, count, timestamp
                FROM sensor_events
                WHERE alarm_system_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (alarm_system_id, limit),
            )
        rows = cur.fetchall()
        events: List[Dict] = []
        for device_id, event_type, count, timestamp in rows:
            events.append(
                {
                    "device_id": device_id,
                    "event_type": event_type,
                    "count": int(count),
                    "timestamp": float(timestamp),
                }
            )
        return events
    except psycopg2.errors.UndefinedTable:
        # If table does not exist yet, just behave as "no history"
        conn.rollback()
        return []
    except Exception as e:
        print(f"Event history load failed: {e}")
        conn.rollback()
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

