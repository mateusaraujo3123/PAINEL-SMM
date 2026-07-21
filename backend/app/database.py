# backend/app/database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# 1. Força o uso do volume da Railway se estiver rodando na nuvem.
# O Railway sempre injeta variáveis de ambiente como RAILWAY_ENVIRONMENT.
if os.getenv("RAILWAY_ENVIRONMENT"):
    VOLUME_DIR = "/data"
else:
    # Fallback seguro para o seu computador local
    VOLUME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Garante que a pasta exista (necessário para o ambiente local ou se o volume iniciar vazio)
os.makedirs(VOLUME_DIR, exist_ok=True)

DB_PATH = os.path.join(VOLUME_DIR, "smm_panel.db")

# String de conexão imune a novos deploys
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, connect_args={"timeout": 30})

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# 2. Remoção do commit global automático que causava travamentos em rotas de leitura
async def get_db():
    async with async_session() as session:
        yield session
