from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt 
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)

def create_access_token(subject: str ) -> str:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": issued_at.timestamp(),
        "exp": expires_at.timestamp(),
        "jti": str(uuid4())
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={'verify_exp': False}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if "jti" not in payload or "exp" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    exp = payload["exp"]
    
    if isinstance(exp, int):
        payload["exp"] = datetime.fromtimestamp(exp, tz=UTC)
    return payload