"""Sensor display names per home (admin-editable; no physical location)."""
from typing import List
from db import connectToDB


def get_sensor_labels(alarm_system_id: int) -> List[str]:
    """Return ordered list of sensor labels for this home. Positions 0,1,2,..."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT label FROM sensor_labels
            WHERE alarm_system_id = %s
            ORDER BY position
            """,
            (alarm_system_id,),
        )
        return [row[0] for row in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def set_sensor_labels(alarm_system_id: int, labels: List[str]) -> bool:
    """Replace all sensor labels for this home. labels[i] = display name for position i."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM sensor_labels WHERE alarm_system_id = %s",
            (alarm_system_id,),
        )
        for pos, label in enumerate(labels):
            if label and str(label).strip():
                cur.execute(
                    "INSERT INTO sensor_labels (alarm_system_id, position, label) VALUES (%s, %s, %s)",
                    (alarm_system_id, pos, str(label).strip()),
                )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"set_sensor_labels failed: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
