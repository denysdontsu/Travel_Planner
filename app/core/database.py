from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# App
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL,
                             echo=settings.DEBUG,
                             pool_pre_ping=True)

async_session_maker = async_sessionmaker(engine,
                                         expire_on_commit=False,
                                         class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide async database session for dependency injection.

    Yields:
        AsyncSession: Database session that will be automatically closed
    """
    async with async_session_maker() as session:
        yield session

db_dependency = Annotated[AsyncSession, Depends(get_db)]
"""Database session dependency. Use in endpoint signatures."""