from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings

engine = create_async_engine(settings.database_url, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
