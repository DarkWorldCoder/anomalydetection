from datetime import datetime 
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


from app.db.base import Base
from backend.app.db.timestamp import TimestampMixin

class User(Base,TimestampMixin):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(default=True)
    
    @classmethod
    def create(cls, full_name: str, email: str, hashed_password: str) -> "User":
        return cls(
            full_name=full_name,
            email=email,
            hashed_password=hashed_password
        )