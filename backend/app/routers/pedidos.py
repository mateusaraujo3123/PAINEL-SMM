# backend/app/routers/pedidos.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx  # Cliente HTTP assíncrono para falar com a API mãe
from backend.app.database import get_db
from backend.app.routers.auth import obter_usuario_logado # Para verificar quem está comprando

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

# Pydantic Schema Alinhado perfeitamente com o envio do seu JavaScript
class PedidoSchema(BaseModel):
    service_id: int
    link: str
    quantity: int

# CONFIGURAÇÃO DA API PROVEDORA (Substitua pelos dados da sua API mãe real)
API_PROVEDOR_URL = "https://api-provedor-smm.com"
API_PROVEDOR_KEY = "SUA_CHAVE_DA_API_MAE"

# Tabela comercial de preços de custo (Sincronizada com os valores do seu select no HTML)
PRECOS_PAINEL = {
    101: 12.50,  # ID 101 -> R$ 12,50 por 1000 seguidores
    102: 8.90    # ID 102 -> R$ 8,90 por 1000 seguidores
}

@router.post("/criar", status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    request: Request, 
    pedido: PedidoSchema, 
    db: AsyncSession = Depends(get_db)
):
    """Recebe o pedido, checa e debita o saldo, e despacha para o provedor principal."""
    
    # 1. VALIDAÇÃO DE SEGURANÇA: Bloqueia o pedido se o usuário não estiver logado
    try:
        usuario = await obter_usuario_logado(request, db=db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Sessão inválida ou expirada. Faça login novamente."
        )

    # 2. VALIDAÇÃO COMERCIAL DE CUSTO: Descobre quanto o pedido vai custar
    preco_por_mil = PRECOS_PAINEL.get(pedido.service_id)
    if not preco_por_mil:
        raise HTTPException(status_code=400, detail="O serviço selecionado é inválido ou não existe.")

    custo_total = (pedido.quantity / 1000) * preco_por_mil

    # 3. VALIDAÇÃO DE SALDO: Verifica se o cliente tem dinheiro suficiente no banco local
    if usuario.saldo < custo_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Saldo insuficiente. Este pedido custa R$ {custo_total:.2f} e você possui R$ {usuario.saldo:.2f}."
        )

    # 4. Monta o payload no padrão exato exigido pelas APIs SMM mundiais
    payload_provedor = {
        "key": API_PROVEDOR_KEY,
        "action": "add",
        "service": pedido.service_id,
        "link": pedido.link,
        "quantity": pedido.quantity
    }
    
    # 5. Faz o disparo assíncrono para a API Mãe SMM
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_PROVEDOR_URL, data=payload_provedor, timeout=10.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="O provedor SMM principal demorou a responder.")
                
            dados_retorno = response.json()
            
            # Se a API mãe recusar a operação (ex: link quebrado, erro do servidor delas)
            if "error" in dados_retorno:
                raise HTTPException(status_code=400, detail=dados_retorno["error"])
                
            # 6. REGRA DE NEGÓCIO: Se a API mãe aceitou, debita o dinheiro da carteira do cliente no SQLite
            usuario.saldo -= custo_total
            db.add(usuario)
            await db.commit() # Salva a nova alteração de saldo no banco de dados

            # Retorno mapeado para o JavaScript ler e exibir no alert()
            return {
                "status": "sucesso",
                "order_id": dados_retorno.get("order"),
                "mensagem": "Seu pedido foi enviado e já está em processamento!"
            }
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Falha de conexão com o servidor de distribuição.")
