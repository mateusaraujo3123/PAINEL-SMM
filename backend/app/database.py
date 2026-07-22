import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# URL do seu banco Postgres da Railway com o driver assíncrono (asyncpg) incluído
DATABASE_URL = "postgresql+asyncpg://postgres:CTnFzqnYvjQzGufkJEnlHbabmrLSCJFY@postgres.railway.internal:5432/railway"

# Criação do motor de conexão assíncrono para o Postgres
engine = create_async_engine(DATABASE_URL, connect_args={})

# Configuração do gerador de sessões do banco de dados
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# Função que distribui as conexões para as rotas do seu FastAPI
async def get_db():
    async with async_session() as session:
        yield session
