# backend/app/database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# Aponta para o volume persistente '/data' montado na nuvem da Railway
# Caso esteja rodando localmente no seu PC, ele cria uma pasta chamada 'data' automaticamente
VOLUME_DIR = "/data"

if not os.path.exists(VOLUME_DIR):
    # Fallback de segurança para desenvolvimento local no seu computador
    VOLUME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(VOLUME_DIR, "smm_panel.db")

# String de conexão imune a novos deploys e reinícios de container
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, connect_args={"timeout": 30})

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
        await session.commit()
