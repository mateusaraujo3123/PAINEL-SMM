# backend/app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_session, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Caminho absoluto fixo para evitar que a Railway apague o banco nos deploys
DATABASE_URL = "sqlite+aiosqlite:////app/smm_panel.db"

from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine(DATABASE_URL, connect_args={"timeout": 30})

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
        await session.commit()
