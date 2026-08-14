# Database bootstrap code centralizes SQLAlchemy metadata and session lifecycle for repositories.
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


settings = get_settings()
# A pipeline run holds a session across minutes of LLM and image calls, so the
# SQLAlchemy defaults (5 + 10 overflow) were exhausted by a handful of concurrent
# runs and unrelated requests then failed auth with a pool timeout.
engine = create_async_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout_seconds,
    pool_recycle=1800,
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    # Yields an async SQLAlchemy session to FastAPI and closes the request-scoped DB context afterward.
    async with AsyncSessionLocal() as session:
        yield session
