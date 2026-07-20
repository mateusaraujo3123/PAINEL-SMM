from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Banco de dados local em arquivo. O prefixo +aiosqlite garante a assincronia.
DATABASE_URL = "sqlite+aiosqlite:///./smm_panel.db"

# Cria o motor de execução de alta performance
engine = create_async_engine(DATABASE_URL, echo=False)

# Configura a fábrica de sessões assíncronas
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Classe base para criar as tabelas
Base = declarative_base()

# Função que abre e fecha a conexão automaticamente nas rotas
async def get_db():
    async with async_session() as session:
        yield session
