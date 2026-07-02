# Third-party
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# App
from app.core.config import settings

engine = create_async_engine(settings.database_url,
                             echo=settings.DEBUG,
                             pool_pre_ping=True)

async_session_maker = async_sessionmaker(engine,
                                         expire_on_commit=False,
                                         class_=AsyncSession)

class Base(DeclarativeBase):
    pass