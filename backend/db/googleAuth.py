from db import connectToDB
import psycopg2
import bcrypt
from typing import Optional, Dict

# In-memory store for dev when PostgreSQL is not running (users lost on restart)
_dev_users: Dict[str, Dict] = {}
_dev_next_id = 1


def _find_or_create_google_user_dev(google_id: str, email: str, name: str) -> Dict:
    """Fallback when DB is unavailable: in-memory user store (dev only)."""
    global _dev_next_id
    if email in _dev_users:
        return _dev_users[email]
    user = {
        "id": _dev_next_id,
        "email": email,
        "name": name or email.split("@")[0],
    }
    _dev_next_id += 1
    _dev_users[email] = user
    return user


def _find_google_user_dev_only(email: str) -> Optional[Dict]:
    """Look up user in dev store only; no create. Returns None if not found."""
    return _dev_users.get(email)


def find_google_user_only(google_id: str, email: str, name: str) -> Optional[Dict]:
    """
    Find an existing user by email (Google OAuth). Does NOT create.
    Returns user dict or None if not found.
    """
    conn = None
    try:
        conn = connectToDB.connectToDB()
        if conn is None:
            return _find_google_user_dev_only(email)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, username FROM user_table WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()
        if user:
            user_id, user_email, username = user
            return {
                "id": user_id,
                "email": user_email,
                "name": username or name,
            }
        return None
    except psycopg2.OperationalError:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return _find_google_user_dev_only(email)
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        print(f"Error in find_google_user_only: {e}")
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def find_or_create_google_user(google_id: str, email: str, name: str) -> Optional[Dict]:
    """
    Find or create a user from Google OAuth.
    Returns user dict with id, email, name, or None if error.
    When PostgreSQL is unavailable, falls back to in-memory store (dev only).
    """
    conn = None
    try:
        conn = connectToDB.connectToDB()
        if conn is None:
            print("Database connection returned None; using dev in-memory store")
            return _find_or_create_google_user_dev(google_id, email, name)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, username FROM user_table WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()

        if user:
            user_id, user_email, username = user
            return {
                "id": user_id,
                "email": user_email,
                "name": username or name,
            }
        else:
            import secrets

            random_password = secrets.token_urlsafe(32)
            password_hash = bcrypt.hashpw(
                random_password.encode(),
                bcrypt.gensalt(),
            ).decode()
            username = email.split("@")[0][:100]

            cursor.execute(
                """
                INSERT INTO user_table (username, email, alarm_system_id, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, username
                """,
                (username, email, None, password_hash),
            )
            new_user = cursor.fetchone()
            conn.commit()
            if new_user:
                user_id, user_email, username = new_user
                return {
                    "id": user_id,
                    "email": user_email,
                    "name": username or name,
                }

    except psycopg2.OperationalError:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        print(
            "PostgreSQL not available (connection refused). Using dev in-memory store for Google OAuth."
        )
        return _find_or_create_google_user_dev(google_id, email, name)
    except psycopg2.IntegrityError:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        try:
            cursor.execute(
                "SELECT id, email, username FROM user_table WHERE email = %s",
                (email,),
            )
            user = cursor.fetchone()
            if user:
                user_id, user_email, username = user
                return {
                    "id": user_id,
                    "email": user_email,
                    "name": username or name,
                }
        except Exception:
            pass
        return None
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error in find_or_create_google_user: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
