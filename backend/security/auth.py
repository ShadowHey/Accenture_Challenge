from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from backend.queue.queue_monitor import queue_manager
import logging

security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def verify_hospital(credentials: HTTPBasicCredentials = Security(security)):
    """
    Verifies hospital credentials against the Supabase `hospitals` table.
    Expects username = hospital_code, password = hospital_password.
    """
    if not queue_manager.supabase:
        raise HTTPException(status_code=500, detail="Database not initialized")

    hospital_code = credentials.username
    password = credentials.password

    try:
        res = queue_manager.supabase.table('hospitals').select('*').eq('hospital_code', hospital_code).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect hospital code or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        hospital = res.data[0]
        if not verify_password(password, hospital['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect hospital code or password",
                headers={"WWW-Authenticate": "Basic"},
            )
            
        return hospital
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error authenticating hospital: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
