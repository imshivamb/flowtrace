from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)