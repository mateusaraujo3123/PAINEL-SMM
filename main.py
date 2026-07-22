from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx  # Cliente HTTP assíncrono para falar com a API mãe
import logging
from backend.app.database import get_db
from backend.app.routers.auth import obter_usuario_logado # Para verificar quem está comprando
from backend.app.models.models import Usuario, Pedido  # Seus modelos unificados

logger = logging.getLogger("smm_pedidos")
router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

# Pydantic Schema Alinhado perfeitamente com o envio do seu JavaScript
class PedidoSchema(BaseModel):
    service_id: int
    link: str = Field(..., min_length=5)
    quantity: int = Field(..., gte=1)

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
    """Recebe o pedido, checa e debita o saldo com Lock, e despacha para o provedor principal."""
    
    # 1. VALIDAÇÃO DE SEGURANÇA: Bloqueia o pedido se o usuário não estiver logado
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Sessão inválida ou expirada. Faça login novamente."
        )

    # 2. VALIDAÇÃO COMERCIAL DE CUSTO: Descobre quanto o pedido vai custar
    preco_por_mil = PRECOS_PAINEL.get(pedido.service_id)
    if not preco_por_mil:
        raise HTTPException(status_code=400, detail="O serviço selecionado é inválido ou não existe.")

    custo_total = round((pedido.quantity / 1000) * preco_por_mil, 4)

    # 3. VALIDAÇÃO DE SALDO COM LOCK (Garante consulta limpa e segura no SQLite)
    async with db.begin():
        query = select(Usuario).where(Usuario.id == usuario_sessao.id).with_for_update()
        resultado = await db.execute(query)
        usuario_real = resultado.scalar_one_or_none()

        if not usuario_real or usuario_real.saldo < custo_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Saldo insuficiente. Este pedido custa R$ {custo_total:.2f} e você possui R$ {usuario_sessao.saldo:.2f}."
            )

        # 4. REGRA DE NEGÓCIO: Debita o dinheiro da carteira local temporariamente antes da chamada de rede
        usuario_real.saldo = round(usuario_real.saldo - custo_total, 4)
        
        # 5. REGISTRO LOCAL INICIAL: Salva a ordem como "Processando"
        novo_pedido = Pedido(
            usuario_id=usuario_real.id,
            servico_id=pedido.service_id,
            link=pedido.link,
            quantidade=pedido.quantity,
            custo_total=custo_total,
            status="Processando"
        )
        db.add(novo_pedido)
        await db.flush() # Sincroniza sem fechar a transação para fixar o ID do pedido

    # 6. Monta o payload no padrão exato exigido pelas APIs SMM mundiais
    payload_provedor = {
        "key": API_PROVEDOR_KEY,
        "action": "add",
        "service": pedido.service_id,
        "link": pedido.link,
        "quantity": pedido.quantity
    }
    
    # 7. Faz o disparo assíncrono para a API Mãe SMM
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_PROVEDOR_URL, data=payload_provedor, timeout=12.0)
            
            if response.status_code != 200:
                # Estorno automático em caso de falha de resposta da API mãe
                async with db.begin():
                    novo_pedido.status = "Cancelado"
                    usuario_real.saldo = round(usuario_real.saldo + custo_total, 4)
                raise HTTPException(status_code=502, detail="O provedor SMM principal demorou a responder.")
                
            dados_retorno = response.json()
            
            # Se a API mãe recusar a operação (ex: link quebrado, erro do servidor delas)
            if "error" in dados_retorno:
                async with db.begin():
                    novo_pedido.status = "Cancelado"
                    usuario_real.saldo = round(usuario_real.saldo + custo_total, 4)
                raise HTTPException(status_code=400, detail=dados_retorno["error"])
                
            # SUCESSO: Confirma o processamento e anexa o ID externo gerado
            async with db.begin():
                novo_pedido.api_order_id = dados_retorno.get("order")
                novo_pedido.status = "Em Processamento"

            return {
                "status": "sucesso",
                "order_id": novo_pedido.id,
                "api_order_id": novo_pedido.api_order_id,
                "mensagem": "Seu pedido foi enviado e já está em processamento!"
            }
            
        except httpx.RequestError:
            # Estorno automático em caso de falha de conexão física/infraestrutura
            async with db.begin():
                novo_pedido.status = "Cancelado"
                usuario_real.saldo = round(usuario_real.saldo + custo_total, 4)
            raise HTTPException(status_code=503, detail="Falha de conexão com o servidor de distribuição.")


@router.get("/historico", status_code=status.HTTP_200_OK)
async def obter_historico_pedidos(request: Request, db: AsyncSession = Depends(get_db)):
    """Busca todos os pedidos salvos do usuário autenticado para alimentar a tabela."""
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(status_code=401, detail="Sessão expirada. Faça login novamente.")

    query = select(Pedido).where(Pedido.usuario_id == usuario_sessao.id).order_by(Pedido.id.desc())
    resultado = await db.execute(query)
    pedidos = resultado.scalars().all()

    lista_pedidos = []
    for p in pedidos:
        nome_servico = f"[ID {p.servico_id}] Serviço SMM"
        if p.servico_id == 101:
            nome_servico = "[ID 101] Insta Seguidores Brasileiros"
        elif p.servico_id == 102:
            nome_servico = "[ID 102] Insta Curtidas Mundiais"

        lista_pedidos.append({
            "id": p.id,
            "servico": nome_servico,
            "link": p.link,
            "quantidade": f"{p.quantidade:,}".replace(",", "."),
            "custo": f"R$ {p.custo_total:.2f}".replace(".", ","),
            "status": p.status
        })

    return lista_pedidos


@router.get("/servicos/lista")
async def obter_lista_servicos_provedor():
    """Busca a tabela de serviços diretamente na API Mãe SMM para alimentar o painel."""
    params_provedor = {
        "key": API_PROVEDOR_KEY,
        "action": "services"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_PROVEDOR_URL, data=params_provedor, timeout=10.0)
            if response.status_code != 200:
                return []
            return response.json()
        except httpx.RequestError:
            return []
