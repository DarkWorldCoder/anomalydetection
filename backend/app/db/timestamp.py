from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
class TimestampMixin:
    # Notice: func.now() has NO parentheses here for the Python-side default
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),        # Generates time via DB on insert
        server_default=func.now(), # Sets the SQL constraint (e.g., DEFAULT NOW())
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        server_default=func.now(),
        onupdate=func.now(),       # Automatically updates timestamp on SQL UPDATE statements
        nullable=False
    )