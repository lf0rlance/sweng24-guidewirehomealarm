"""
Run admin/roles migration on the DB this app connects to (same connectToDB as the rest of the app).
Call once at startup so the table is updated even if the standalone migration script hit a different DB.
"""
from db import connectToDB


def ensure_user_table_phone_and_role():
    """Add phone and role columns to user_table if missing. Idempotent."""
    conn = None
    try:
        conn = connectToDB.connectToDB()
        cur = conn.cursor()
        cur.execute(
            "ALTER TABLE user_table ADD COLUMN IF NOT EXISTS phone VARCHAR(30)"
        )
        cur.execute(
            "ALTER TABLE user_table ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'"
        )
        cur.execute("ALTER TABLE user_table ALTER COLUMN role SET DEFAULT 'user'")
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ensure_schema (user_table): {e}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def ensure_alarm_system_name():
    """Add display name column to alarm_system_table if missing. Idempotent."""
    conn = None
    try:
        conn = connectToDB.connectToDB()
        cur = conn.cursor()
        cur.execute(
            "ALTER TABLE alarm_system_table ADD COLUMN IF NOT EXISTS name VARCHAR(120)"
        )
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ensure_schema (alarm_system name): {e}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def ensure_sensor_labels_and_device_last_seen():
    """Create sensor_labels and device_last_seen tables if missing. Idempotent."""
    conn = None
    try:
        conn = connectToDB.connectToDB()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_labels (
                alarm_system_id INT NOT NULL REFERENCES alarm_system_table (alarm_system_id) ON DELETE CASCADE,
                position INT NOT NULL,
                label TEXT NOT NULL,
                PRIMARY KEY (alarm_system_id, position)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS device_last_seen (
                microcontroller_id INT PRIMARY KEY REFERENCES microcontroller (microcontroller_id) ON DELETE CASCADE,
                last_seen DOUBLE PRECISION NOT NULL
            )
        """)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ensure_schema (sensor_labels/device_last_seen): {e}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def ensure_access_control_tables():
    """
    Create alarm_system_memberships and extend fcm_tokens to be user-scoped.
    Also backfills memberships for existing users (treat existing pairing as owner).
    Idempotent.
    """
    conn = None
    try:
        conn = connectToDB.connectToDB()
        cur = conn.cursor()

        # User-scoped FCM tokens (so we can suppress notifications for limited roles)
        cur.execute(
            """
            ALTER TABLE fcm_tokens
            ADD COLUMN IF NOT EXISTS user_id INT REFERENCES user_table(id) ON DELETE CASCADE
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_fcm_tokens_system_user ON fcm_tokens (alarm_system_id, user_id)"
        )

        # Memberships and permissions per home/system
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alarm_system_memberships (
                user_id INT NOT NULL REFERENCES user_table (id) ON DELETE CASCADE,
                alarm_system_id INT NOT NULL REFERENCES alarm_system_table (alarm_system_id) ON DELETE CASCADE,
                access_level TEXT NOT NULL,
                can_arm BOOLEAN NOT NULL DEFAULT FALSE,
                can_disarm BOOLEAN NOT NULL DEFAULT FALSE,
                can_view_events BOOLEAN NOT NULL DEFAULT FALSE,
                can_receive_notifications BOOLEAN NOT NULL DEFAULT FALSE,
                can_manage_users BOOLEAN NOT NULL DEFAULT FALSE,
                created_at DOUBLE PRECISION,
                PRIMARY KEY (user_id, alarm_system_id)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_memberships_system ON alarm_system_memberships (alarm_system_id)"
        )

        # Backfill: if a user is paired via user_table.alarm_system_id, treat them as owner unless already present.
        # This keeps existing flows working even before the UI exposes memberships.
        cur.execute(
            """
            INSERT INTO alarm_system_memberships (
                user_id, alarm_system_id, access_level,
                can_arm, can_disarm, can_view_events, can_receive_notifications, can_manage_users,
                created_at
            )
            SELECT
                u.id,
                u.alarm_system_id,
                'owner',
                TRUE, TRUE, TRUE, TRUE, TRUE,
                EXTRACT(EPOCH FROM NOW())
            FROM user_table u
            WHERE u.alarm_system_id IS NOT NULL
            ON CONFLICT (user_id, alarm_system_id) DO NOTHING
            """
        )

        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ensure_schema (access control): {e}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def ensure_one_time_disarm_codes_table():
    """Create one_time_disarm_codes table if missing. Idempotent."""
    conn = None
    try:
        conn = connectToDB.connectToDB()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS one_time_disarm_codes (
              id BIGSERIAL PRIMARY KEY,
              alarm_system_id INT NOT NULL REFERENCES alarm_system_table (alarm_system_id) ON DELETE CASCADE,
              code TEXT NOT NULL,
              created_by_user_id INT NOT NULL REFERENCES user_table (id) ON DELETE CASCADE,
              created_at DOUBLE PRECISION NOT NULL,
              expires_at DOUBLE PRECISION NOT NULL,
              used_at DOUBLE PRECISION,
              used_by_user_id INT REFERENCES user_table (id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_disarm_codes_system_code ON one_time_disarm_codes (alarm_system_id, code)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_disarm_codes_system_unused ON one_time_disarm_codes (alarm_system_id, used_at)"
        )
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ensure_schema (one_time_disarm_codes): {e}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def run_startup_migration():
    """Call at app startup to ensure DB has phone, role, admin tables, and alarm_system name."""
    ensure_user_table_phone_and_role()
    ensure_alarm_system_name()
    ensure_sensor_labels_and_device_last_seen()
    ensure_access_control_tables()
    ensure_one_time_disarm_codes_table()
