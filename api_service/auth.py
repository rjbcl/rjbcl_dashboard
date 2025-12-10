# auth.py
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from dotenv import load_dotenv
from database import get_postgres_connection

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-prod")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

def authenticate_user(username: str, password: str):
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash, is_active FROM public.kyc_api_users WHERE username = %s LIMIT 1",
        (username,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    stored_hash, is_active = row
    if not is_active:
        return None

    try:
        ph.verify(stored_hash, password)
    except argon2_exceptions.VerifyMismatchError:
        return None
    except Exception:
        return None

    return {"username": username}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}
