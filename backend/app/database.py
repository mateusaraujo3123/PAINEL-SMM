# backend/app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_session, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# Cria um caminho absoluto nativo seguro que funciona em qualquer servidor Linux/Railway
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "smm_panel.db")

# String de conexão limpa utilizando a conversão automática do Python
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, connect_args={"timeout": 30})

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
        await session.commit()
