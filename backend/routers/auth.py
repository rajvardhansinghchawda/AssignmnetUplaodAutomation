from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from google.oauth2 import id_token
from google.auth.transport import requests

import db
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/google")

# ── Models ───────────────────────────────────────────────────────────────────

class GoogleLoginRequest(BaseModel):
    credential: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# ── Helpers ──────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/google", response_model=Token)
async def google_auth(request: GoogleLoginRequest):
    try:
        # Verify the Google ID token
        id_info = id_token.verify_oauth2_token(
            request.credential, 
            requests.Request(), 
            settings.google_client_id
        )

        email = id_info['email']
        full_name = id_info.get('name')
        picture = id_info.get('picture')

        # Check if user exists
        user = await db.get_user_by_email(email)
        if not user:
            # Create user if it doesn't exist
            user_id = await db.create_user(email, full_name, picture)
            user = await db.get_user_by_id(user_id)
        else:
            # Optionally update user info if it changed
            pass

        # Create local JWT
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "picture": current_user.get("picture")
    }
