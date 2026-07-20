from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Banco de dados SQLite assíncrono local por arquivo
DATABASE_URL = "sqlite+aiosqlite:///./smm_panel.db"

# Motor de alta performance para execução de queries
engine = create_async_engine(DATABASE_URL, echo=False)

# Fábrica de sessões assíncronas para as rotas
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Classe base para os modelos das tabelas
Base = declarative_base()

# Dependência para abrir e fechar conexões automaticamente
async def get_db():
    async with async_session() as session:
        yield session
