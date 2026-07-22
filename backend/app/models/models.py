from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) 
    saldo = Column(Float, default=0.0) 

    # Relacionamento de via dupla com os pedidos do usuário
    pedidos = relationship("Pedido", back_populates="usuario")


class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=False, index=True)
    preco_por_mil = Column(Float, nullable=False)
    minimo = Column(Integer, nullable=False, default=10)
    maximo = Column(Integer, nullable=False, default=10000)
    
    # Integração com Provedores SMM Externos (Opcional por serviço)
    provedor_api_url = Column(String, nullable=True)
    provedor_servico_id = Column(Integer, nullable=True)


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)
    link = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
    custo_total = Column(Float, nullable=False)
    status = Column(String, default="Pendente") # Pendente, Processando, Concluido, Cancelado, Parcial
    api_order_id = Column(Integer, nullable=True) # ID gerado na API externa (Perfect Panel)
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos para consultas eficientes (Joins assíncronos)
    usuario = relationship("Usuario", back_populates="pedidos")
    servico = relationship("Servico")
