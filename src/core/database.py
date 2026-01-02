from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from  src.models import Base

from .config import DATABASE_URL


engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    pool_size=5,
    max_overflow=10
    )

AssyncSessionLocal = async_sessionmaker(
    engine, 
    expire_on_commit=False,  # не инвалидировать объекты после commit
    class_=AsyncSession
) 

async def get_db_session():
    async with AssyncSessionLocal() as session:
        yield session

