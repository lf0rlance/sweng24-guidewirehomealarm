import bcrypt
import psycopg2
from typing import Optional

from db import connectToDB
from db.home_roles import HOME_ROLES, count_users_in_home, home_has_owner


def insertUserInDB(
    username: str,
    email: str,
    alarm_system_id: int | None,
    password: str,
    role: str = "user",
) -> bool:
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
            VALUES(%s, %s, %s, %s, %s)
            """,
            (username, email, alarm_system_id, password_hash, role)
        )

        conn.commit()
        return True

    except psycopg2.IntegrityError:
        conn.rollback()
        return False

    finally:
        if conn:
            conn.close()


def _resolve_home_role_for_insert(alarm_system_id: int, requested: Optional[str]) -> Optional[str]:
    """First user in a home is always owner; only one owner per home."""
    n = count_users_in_home(alarm_system_id)
    if n == 0:
        return "owner"
    hr = (requested or "spouse").strip().lower()
    if hr not in HOME_ROLES:
        hr = "spouse"
    if hr == "owner":
        if home_has_owner(alarm_system_id):
            return None
    return hr


def insert_user_by_admin(
    username: str,
    email: str,
    password: str,
    alarm_system_id: int,
    phone: Optional[str] = None,
    home_role: Optional[str] = None,
) -> bool:
    """Create a homeowner user (role=user) for a home; used by admin. No home address stored."""
    hr = _resolve_home_role_for_insert(alarm_system_id, home_role)
    if hr is None:
        return False
    conn = connectToDB.connectToDB()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO user_table (username, email, alarm_system_id, password_hash, role, phone, home_role)
            VALUES (%s, %s, %s, %s, 'user', %s, %s)
            """,
            (username, email, alarm_system_id, password_hash, phone or None, hr),
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
    home_role: Optional[str] = None,
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
        if home_role is not None:
            h = home_role.strip().lower()
            if h not in HOME_ROLES:
                return False
            if h == "owner":
                cur.execute(
                    """
                    SELECT id FROM user_table
                    WHERE alarm_system_id = %s AND COALESCE(home_role, 'owner') = 'owner' AND id != %s
                    """,
                    (alarm_system_id, user_id),
                )
                if cur.fetchone():
                    return False
            updates.append("home_role = %s")
            args.append(h)
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


def link_existing_user_to_home(
    email: str,
    alarm_system_id: int,
    password: Optional[str] = None,
    home_role: Optional[str] = None,
) -> str:
    """
    Attach an existing account (e.g. Google signup) to this home.
    Returns '' on success, or 'not_found', 'already_other_home', or 'update_failed'.
    Optional password sets/resets hash so the user can also use email/password login.
    """
    conn = connectToDB.connectToDB()
    email_norm = email.strip().lower()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, alarm_system_id FROM user_table WHERE lower(trim(email)) = %s",
            (email_norm,),
        )
        row = cur.fetchone()
        if not row:
            return "not_found"
        uid, current_home = row[0], row[1]
        if current_home is not None and int(current_home) != int(alarm_system_id):
            return "already_other_home"

        if current_home is None:
            hr = _resolve_home_role_for_insert(alarm_system_id, home_role)
            if hr is None:
                return "owner_exists"
        else:
            hr = None
        updates = []
        args: list = []
        if current_home is None:
            updates.append("alarm_system_id = %s")
            args.append(alarm_system_id)
            updates.append("home_role = %s")
            args.append(hr)
        pwd = (password or "").strip()
        if pwd:
            updates.append("password_hash = %s")
            args.append(bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode())
        if not updates:
            return ""
        args.append(uid)
        cur.execute(
            f"UPDATE user_table SET {', '.join(updates)} WHERE id = %s",
            args,
        )
        conn.commit()
        if cur.rowcount > 0:
            return ""
        return "update_failed"
    except Exception as e:
        conn.rollback()
        print(f"link_existing_user_to_home: {e}")
        return "update_failed"
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
        try:
            cur.execute(
                """
                UPDATE user_table SET alarm_system_id = NULL, home_role = NULL
                WHERE id = %s AND alarm_system_id = %s
                """,
                (user_id, alarm_system_id),
            )
        except Exception:
            conn.rollback()
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
