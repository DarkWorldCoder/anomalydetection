from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession 
from app.services.auth_service import get_user_by_email, authenticate_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, create_access_token
from backend.app.db.session import get_db
from app.models.user import User
from app.db.session import get_db
from app.core.responses import success_response
from app.schemas.user import UserRead

from app.api.deps import get_current_user,get_bearer_token
from backend.app.models.revoked_token import RevokedToken
router = APIRouter(prefix="/auth",tags=["Auth"])

@router.post("/register")
async def register_user(payload:RegisterRequest,db:AsyncSession = Depends(get_db)):
    
    # check if user already exists
    existing_user = await get_user_by_email(db,payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    user = User.create(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return success_response(
        message="User registered successfully",
        data=UserRead.model_validate(user)
    )
    
@router.post("/login")
async def login_user(payload:LoginRequest,db:AsyncSession = Depends(get_db)):
    user = await authenticate_user(db,payload.email,payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=str(user.id))
    
    return success_response(
        message="Login successful",
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead.model_validate(user)
        )
    )
    
@router.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    return success_response(
        message="Current user retrieved successfully",
        data=UserRead.model_validate(current_user)
    )
    
@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_bearer_token),
    db: AsyncSession = Depends(get_db)
):
    payload = decode_access_token(token)
    jti = payload.get("jti")
    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    revoked_token = RevokedToken(jti=jti, user_id=current_user.id)
    db.add(revoked_token)
    await db.commit()
    
    return success_response(message="Logout successful")