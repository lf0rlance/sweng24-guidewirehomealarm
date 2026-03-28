#
import jwt
from datetime import datetime, timedelta, timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

import bcrypt
from app.config import settings
from db.googleAuth import find_or_create_google_user, find_google_user_only, get_user_by_email_for_password_login
from app.services.otp_service import generate_otp, send_otp_email, verify_otp


def verify_google_token(id_token_str: str):
    idinfo = id_token.verify_oauth2_token(
        id_token_str,
        google_requests.Request(),
        settings.google_client_id
    )
    if idinfo["aud"] != settings.google_client_id:
        raise ValueError("Invalid audience")
    return idinfo


def build_user_response(user: dict):
    role = user.get("role") or "user"
    token = jwt.encode(
        {"userId": user["id"], "email": user["email"], "role": role},
        settings.jwt_secret,
        algorithm="HS256"
    )
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": role,
            "phone": user.get("phone"),
        }
    }


def signup_user(idToken: str):
    idinfo = verify_google_token(idToken)
    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name", email.split("@")[0])
    if find_google_user_only(google_id, email, name):
        raise Exception("Account already exists")
    user = find_or_create_google_user(google_id, email, name)
    return build_user_response(user)


def signin_user(idToken: str):
    idinfo = verify_google_token(idToken)
    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name", email.split("@")[0])
    user = find_google_user_only(google_id, email, name)
    if not user:
        raise Exception("Account does not exist")
    return build_user_response(user)


def signin_user_mfa(idToken: str):
    idinfo = verify_google_token(idToken)
    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name", email.split("@")[0])
    user = find_google_user_only(google_id, email, name)
    if not user:
        raise Exception("Account does not exist")
    code = generate_otp(email)
    send_otp_email(email, code)
    return {"mfa_required": True, "email": email}


def verify_otp_and_signin(email: str, code: str):
    if not verify_otp(email, code):
        raise Exception("Invalid or expired code")
    user = find_google_user_only("", email, "")
    if not user:
        raise Exception("User not found")
    return build_user_response(user)


def login_with_password(email: str, password: str):
    """Login for admin-created users (email + password). Returns same shape as Google auth."""
    row = get_user_by_email_for_password_login(email)
    if not row:
        raise Exception("Account does not exist or sign-in method not available")
    user_dict, password_hash = row
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
        raise Exception("Invalid password")
    return build_user_response(user_dict)
