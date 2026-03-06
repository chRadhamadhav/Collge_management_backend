"""
Async SQLAlchemy engine and session factory.
All database access in the application goes through the AsyncSession provided here.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# Engine is shared application-wide — created once at startup
engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",  # SQL logging in dev only
    pool_pre_ping=True,  # Detect stale connections before using them
    pool_size=10,
    max_overflow=20,
)

# Session factory — each request gets its own session via Depends(get_db)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Prevent lazy-load issues after commit
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.
    Session is automatically closed after the response is sent.
    """
    async with AsyncSessionLocal() as session:
        yield session
