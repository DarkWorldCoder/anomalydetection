from collections.abc import AsyncGenerator 
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    poolclass=NullPool,  # Disable connection pooling for async engines
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Prevents attributes from being expired after commit
    class_=AsyncSession
)

async def get_db() -> AsyncGenerator[AsyncSession,None]:
    async with AsyncSessionLocal() as session:
        yield session
