import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from  database.models import Base

from config import DATABASE_URL

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

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)




async def test():
    async with AssyncSessionLocal() as session:
        async with session.begin():
            pass

        
if __name__ == "__main__":
    asyncio.run(init_models())
 
