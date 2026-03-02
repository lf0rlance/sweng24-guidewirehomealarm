#
import jwt
from datetime import datetime, timedelta, timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings
from db.googleAuth import find_or_create_google_user, find_google_user_only


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
    if not settings.jwt_secret:
        raise ValueError("JWT secret is not configured")

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "userId": user["id"],
            "email": user["email"],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256"
    )

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
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
