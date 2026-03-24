from db import connectToDB
import psycopg2
import bcrypt
from typing import Optional


def insertUserInDB(username: str, email: str, alarm_system_id: int | None, password: str) -> bool:
    conn = connectToDB.connectToDB()

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_table(username, email, alarm_system_id, password_hash, role)
            VALUES(%s, %s, %s, %s, 'user')
            """,
            (username, email, alarm_system_id, password_hash)
        )

        conn.commit()
        return True

    except psycopg2.IntegrityError:
        conn.rollback()
        return False

    finally:
        if conn:
            conn.close()


def insert_user_by_admin(
    username: str,
    email: str,
    password: str,
    alarm_system_id: int,
    phone: Optional[str] = None,
) -> bool:
    """Create a homeowner user (role=user) for a home; used by admin. No home address stored."""
    conn = connectToDB.connectToDB()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO user_table (username, email, alarm_system_id, password_hash, role, phone)
            VALUES (%s, %s, %s, %s, 'user', %s)
            """,
            (username, email, alarm_system_id, password_hash, phone or None),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_user_by_admin(
    user_id: int,
    alarm_system_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    password: Optional[str] = None,
) -> bool:
    """Update a user in this home (admin only). Only provided fields are updated."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        updates = []
        args = []
        if username is not None:
            updates.append("username = %s")
            args.append(username.strip()[:100])
        if email is not None:
            updates.append("email = %s")
            args.append(email.strip().lower())
        if phone is not None:
            updates.append("phone = %s")
            args.append(phone.strip()[:30] if phone.strip() else None)
        if password is not None and password.strip():
            updates.append("password_hash = %s")
            args.append(bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
        if not updates:
            return True
        args.extend([user_id, alarm_system_id])
        cur.execute(
            f"UPDATE user_table SET {', '.join(updates)} WHERE id = %s AND alarm_system_id = %s",
            args,
        )
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    except Exception as e:
        conn.rollback()
        print(f"update_user_by_admin: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def unlink_user_from_home(user_id: int, alarm_system_id: int) -> bool:
    """Remove user from this home (set alarm_system_id to NULL). Admin only."""
    conn = connectToDB.connectToDB()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE user_table SET alarm_system_id = NULL WHERE id = %s AND alarm_system_id = %s",
            (user_id, alarm_system_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"unlink_user_from_home: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
