import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings
from db.googleAuth import find_or_create_google_user, find_google_user_only
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
    token = jwt.encode(
        {"userId": user["id"], "email": user["email"]},
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
