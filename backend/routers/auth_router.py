import os
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client
import bcrypt

from backend.security.hospital_auth import authenticate_user, create_session_token, invalidate_token, get_current_user

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    hospital_code: str
    password: str

@router.post("/register")
def register(req: RegisterRequest):
    supabase = get_supabase_client()
    res = supabase.table("hospitals").select("*").eq("hospital_code", req.hospital_code).execute()
    if res.data:
        raise HTTPException(status_code=400, detail="Hospital code already exists")
    
    hashed = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    supabase.table("hospitals").insert({
        "name": req.name,
        "hospital_code": req.hospital_code,
        "password_hash": hashed
    }).execute()
    return {"status": "success", "message": "Hospital registered successfully"}

@router.post("/login")
def login(req: LoginRequest):
    try:
        user_info = authenticate_user(req.username, req.password)
        token = create_session_token(user_info["username"], user_info["role"], user_info["hospital_code"])
        
        supabase = get_supabase_client()
        hospital_name = "Unknown Hospital"
        try:
            res = supabase.table("hospitals").select("name").eq("hospital_code", user_info["hospital_code"]).execute()
            if res.data:
                hospital_name = res.data[0]["name"]
        except Exception:
            pass
            
        return {
            "token": token,
            "role": user_info["role"],
            "hospital_code": user_info["hospital_code"],
            "hospital_name": hospital_name,
            "username": user_info["username"]
        }
    except HTTPException:
        supabase = get_supabase_client()
        res = supabase.table("hospitals").select("*").eq("hospital_code", req.username).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        hosp = res.data[0]
        if not bcrypt.checkpw(req.password.encode('utf-8'), hosp['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_session_token(req.username, "HOSPITAL_ADMIN", req.username)
        return {
            "token": token,
            "role": "HOSPITAL_ADMIN",
            "hospital_code": req.username,
            "hospital_name": hosp["name"],
            "username": req.username
        }

@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            invalidate_token(parts[1])
    return {"status": "logged_out"}

@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    hospital_name = "Unknown Hospital"
    try:
        res = supabase.table("hospitals").select("name").eq("hospital_code", user["hospital_code"]).execute()
        if res.data:
            hospital_name = res.data[0]["name"]
    except Exception:
        pass
        
    return {
        "username": user["username"],
        "role": user["role"],
        "hospital_code": user["hospital_code"],
        "hospital_name": hospital_name
    }
