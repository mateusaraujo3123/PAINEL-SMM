from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
import httpx  # Cliente HTTP assíncrono para falar com a API mãe

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

# Pydantic Schema: Valida os dados enviados pelo seu JavaScript
class PedidoSchema(BaseModel):
    servico_id: int
    link: str
    quantidade: int

# CONFIGURAÇÃO DA API PROVEDORA (Substitua pelos dados da sua API mãe)
API_PROVEDOR_URL = "https://api-provedor-smm.com"
API_PROVEDOR_KEY = "SUA_CHAVE_DA_API_MAE"

@router.post("/criar", status_code=status.HTTP_201_CREATED)
async def criar_pedido(pedido: PedidoSchema, db: AsyncSession = Depends(get_db)):
    """Recebe o pedido do painel e despacha para o provedor principal."""
    
    # 1. Monta o payload no padrão que as APIs SMM globais exigem
    payload_provedor = {
        "key": API_PROVEDOR_KEY,
        "action": "add",
        "service": pedido.servico_id,
        "link": pedido.link,
        "quantity": pedido.quantidade
    }
    
    # 2. Faz o disparo assíncrono sem travar a interface do cliente
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_PROVEDOR_URL, data=payload_provedor, timeout=10.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="O provedor SMM principal demorou a responder.")
                
            dados_retorno = response.json()
            
            # Se a API mãe devolver algum erro (ex: saldo insuficiente na API mãe, id inválido)
            if "error" in dados_retorno:
                raise HTTPException(status_code=400, detail=dados_retorno["error"])
                
            # Retorno de sucesso comercial
            return {
                "status": "sucesso",
                "pedido_id_provedor": dados_retorno.get("order"),
                "mensagem": "Seu pedido foi enviado e já está em processamento!"
            }
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Falha de conexão com o servidor de distribuição.")
