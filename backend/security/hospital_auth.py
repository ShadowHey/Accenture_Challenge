import uuid
import time
from typing import Optional, Dict
import bcrypt as _bcrypt
from fastapi import HTTPException, Header, Depends

STAFF_CREDENTIALS = {
    "clinician@H001.hosp": {
        "password_hash": "$2b$12$32JF0AEOIkeSBys2u8WvrOmXIVJN/q1so6irNGR8supjFmQUHL.0K",
        "role": "CLINICIAN",
        "hospital_code": "H001"
    },
    "receptionist@H001.hosp": {
        "password_hash": "$2b$12$b5dyunL9ZJJQSLqFmq0XqeduV55bC9ajlgToGdJ94mmTplku1XLO6",
        "role": "RECEPTIONIST",
        "hospital_code": "H001"
    },
    "clinician@H002.hosp": {
        "password_hash": "$2b$12$Xfeex7VvmShb9WdgbrP7t.tr8XSSQpUpVF3FrowFwhXj4npj516ti",
        "role": "CLINICIAN",
        "hospital_code": "H002"
    },
    "receptionist@H002.hosp": {
        "password_hash": "$2b$12$qKFBvETfn920dj2v2SgTL.t8CqBvfkfOcVN0glRYF9WMOEzI7kdOO",
        "role": "RECEPTIONIST",
        "hospital_code": "H002"
    }
}

active_sessions = {}

def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())

def authenticate_user(username: str, password: str) -> dict:
    user = STAFF_CREDENTIALS.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "username": username,
        "role": user["role"],
        "hospital_code": user["hospital_code"]
    }

def create_session_token(username: str, role: str, hospital_code: str) -> str:
    token = str(uuid.uuid4())
    active_sessions[token] = {
        "username": username,
        "role": role,
        "hospital_code": hospital_code,
        "login_at": time.time()
    }
    return token

def validate_token(token: str) -> dict:
    session = active_sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session

def invalidate_token(token: str):
    if token in active_sessions:
        del active_sessions[token]

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    token = parts[1]
    return validate_token(token)
