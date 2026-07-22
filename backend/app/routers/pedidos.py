from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx
from backend.app.database import get_db
from backend.app.routers.auth import obter_usuario_logado
from backend.app.models.models import Usuario, Pedido

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

class PedidoSchema(BaseModel):
    service_id: int
    link: str = Field(..., min_length=5)
    quantity: int = Field(..., gte=1)

# CONFIGURAÇÃO DA API PROVEDORA
API_PROVEDOR_URL = "https://api-provedor-smm.com"
API_PROVEDOR_KEY = "SUA_CHAVE_DA_API_MAE"

# Tabela comercial de preços de custo (Preço por 1000 envios)
PRECOS_PAINEL = {
    101: 12.50,  # ID 101 -> R$ 12,50 por 1000
    102: 8.90    # ID 102 -> R$ 8,90 por 1000
}

@router.post("/criar", status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    request: Request, 
    pedido: PedidoSchema, 
    db: AsyncSession = Depends(get_db)
):
    """Recebe o pedido, checa e debita o saldo com Lock, e despacha para o provedor."""
    
    # 1. VALIDAÇÃO DE SEGURANÇA
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Sessão inválida ou expirada. Faça login novamente."
        )

    # 2. VALIDAÇÃO COMERCIAL DE CUSTO
    preco_por_mil = PRECOS_PAINEL.get(pedido.service_id)
    if not preco_por_mil:
        raise HTTPException(status_code=400, detail="O serviço selecionado é inválido ou não existe.")

    custo_total = round((pedido.quantity / 1000) * preco_por_mil, 4)

    # 3. LOCK CONCORRENTE DE SALDO (Evita Double-Spending / Cliques Duplos)
    async with db.begin():
        query = select(Usuario).where(Usuario.id == usuario_sessao.id).with_for_update()
        resultado = await db.execute(query)
        usuario = resultado.scalar_one_or_none()

        if not usuario or usuario.saldo < custo_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Saldo insuficiente. Custo: R$ {custo_total:.2f} | Saldo: R$ {usuario.saldo:.2f}."
            )

        # 4. DEBITA O SALDO IMEDIATAMENTE NO BANCO LOCAL
        usuario.saldo = round(usuario.saldo - custo_total, 4)
        
        # 5. SALVA O PEDIDO LOCALMENTE COMO "PROCESSANDO"
        novo_pedido = Pedido(
            usuario_id=usuario.id,
            servico_id=pedido.service_id,
            link=pedido.link,
            quantidade=pedido.quantity,
            custo_total=custo_total,
            status="Processando"
        )
        db.add(novo_pedido)
        await db.flush()

    # 6. DISPARO ASSÍNCRONO PARA A API MÃE SMM (Fora do lock)
    payload_provedor = {
        "key": API_PROVEDOR_KEY,
        "action": "add",
        "service": pedido.service_id,
        "link": pedido.link,
        "quantity": pedido.quantity
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_PROVEDOR_URL, data=payload_provedor, timeout=12.0)
            
            if response.status_code != 200:
                async with db.begin():
                    novo_pedido.status = "Cancelado"
                    usuario.saldo = round(usuario.saldo + custo_total, 4)
                raise HTTPException(status_code=502, detail="O provedor SMM principal demorou a responder.")
                
            dados_retorno = response.json()
            
            if "error" in dados_retorno:
                async with db.begin():
                    novo_pedido.status = "Cancelado"
                    usuario.saldo = round(usuario.saldo + custo_total, 4)
                raise HTTPException(status_code=400, detail=dados_retorno["error"])
                
            # 7. SUCESSO: Vincula o ID retornado pela API Mãe
            async with db.begin():
                novo_pedido.api_order_id = dados_retorno.get("order")
                novo_pedido.status = "Em Processamento"

            return {
                "status": "sucesso",
                "order_id": novo_pedido.id,
                "api_order_id": novo_pedido.api_order_id,
                "novo_saldo": usuario.saldo,
                "mensagem": "Seu pedido foi enviado e já está em processamento!"
            }
            
        except httpx.RequestError:
            async with db.begin():
                novo_pedido.status = "Cancelado"
                usuario.saldo = round(usuario.saldo + custo_total, 4)
            raise HTTPException(status_code=503, detail="Falha de conexão com o servidor de distribuição.")

@router.get("/historico", status_code=status.HTTP_200_OK)
async def obter_historico_pedidos(request: Request, db: AsyncSession = Depends(get_db)):
    """Busca todos os pedidos salvos do usuário autenticado para alimentar o front."""
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
            "quantidade": f"{p.quantity:,}".replace(",", "."),
            "custo": f"R$ {p.custo_total:.2f}".replace(".", ","),
            "status": p.status
        })

    return lista_pedidos

@router.get("/servicos/lista")
async def obter_lista_servicos_provedor():
    """Busca la tabela de serviços diretamente na API Mãe SMM para alimentar o painel."""
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
