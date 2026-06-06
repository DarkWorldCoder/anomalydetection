from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserRead 

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=255)
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Full name cannot be empty or whitespace")
        return value.strip()
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> EmailStr:
        if not value.strip():
            raise ValueError("Email cannot be empty or whitespace")
        return value.strip()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=255)
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return value.strip().lower()
    
class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead