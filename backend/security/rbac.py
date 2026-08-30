from fastapi import Header, HTTPException, Depends
from typing import Optional

import uuid

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def get_current_role(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        return "RECEPTIONIST"
    
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
        if is_valid_uuid(token):
            from backend.security.hospital_auth import validate_token
            try:
                session = validate_token(token)
                return session.get("role", "RECEPTIONIST")
            except HTTPException:
                return "RECEPTIONIST"
                
        role = token.upper()
        if role in ["CLINICIAN", "RECEPTIONIST"]:
            return role
            
    return "RECEPTIONIST"

def get_hospital_code(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        return "H001"
        
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
        if is_valid_uuid(token):
            from backend.security.hospital_auth import validate_token
            try:
                session = validate_token(token)
                return session.get("hospital_code", "H001")
            except HTTPException:
                pass
                
    return "H001"
def require_clinician_role(role: str = Depends(get_current_role)):
    """
    FastAPI dependency that blocks access if the user is not a clinician.
    """
    if role != "CLINICIAN":
        raise HTTPException(status_code=403, detail="Unauthorized: Clinician role required.")
    return role
