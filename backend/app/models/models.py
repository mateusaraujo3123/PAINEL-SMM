from sqlalchemy import Column, Integer, String, Float
from backend.app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # Senha criptografada por segurança
    saldo = Column(Float, default=0.0) # Carteira digital do cliente
