from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_bearer_token, get_current_user
from app.core.responses import success_response
from app.core.security import create_access_token, decode_token_without_exp_validation
from app.db.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenData
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import authenticate_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User.create(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    await db.refresh(user)
    return success_response(
        message="User registered successfully",
        data=UserRead.model_validate(user),
    )


@router.post("/login")
async def login_user(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    data = TokenData(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )
    return success_response(message="Login successful", data=data)


@router.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    return success_response(
        message="Current user fetched successfully",
        data=UserRead.model_validate(current_user),
    )


@router.patch("/me")
async def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.email is not None:
        current_user.email = payload.email

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    await db.refresh(current_user)
    return success_response(
        message="Profile updated successfully",
        data=UserRead.model_validate(current_user),
    )


@router.get("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_bearer_token),
):
    payload = decode_token_without_exp_validation(token)
    revoked_token = RevokedToken(
        jti=payload["jti"],
        user_id=current_user.id,
        expires_at=payload["exp"],
    )
    db.add(revoked_token)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()

    return success_response(message="Logout successful")
