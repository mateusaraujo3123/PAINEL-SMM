from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.database import get_db
from backend.app.routers.auth import obter_usuario_logado
from backend.app.models.models import Usuario, Pedido

# Importação do motor isolado do fornecedor
from backend.app.services.smm_provider import obter_servicos_fornecedor, despachar_ordem_provedor

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

class PedidoSchema(BaseModel):
    service_id: int
    link: str = Field(..., min_length=5)
    quantity: int = Field(..., gte=1)

# =========================================================================
# 📈 CONFIGURAÇÃO COMERCIAL DE PREÇOS (MARGEM DE LUCRO)
# =========================================================================
MULTIPLICADOR_LUCRO = 2.0 
# =========================================================================

@router.get("/servicos-api")
async def listar_servicos_filtrados(request: Request):
    """Obtém os dados brutos da API mãe e estrutura em categorias para o seu front-end."""
    servicos_brutos = await obter_servicos_fornecedor()
    
    if not servicos_brutos or not isinstance(servicos_brutos, list):
        return {} # Evita quebras se o token estiver incorreto ou a API mãe fora do ar
    
    catalogo = {}
    for item in servicos_brutos:
        if not isinstance(item, dict):
            continue
            
        preco_custo = float(item.get("rate", 0.0))
        preco_venda = round(preco_custo * MULTIPLICADOR_LUCRO, 2)
        
        categoria = item.get("category", "Outros Serviços")
        if categoria not in catalogo:
            catalogo[categoria] = []
            
        catalogo[categoria].append({
            "id": int(item.get("service")),
            "nome": item.get("name"),
            "preco": preco_venda,
            "min": int(item.get("min", 100)),
            "max": int(item.get("max", 10000))
        })
    return catalogo

@router.post("/criar", status_code=status.HTTP_201_CREATED)
async def criar_pedido(request: Request, pedido: PedidoSchema, db: AsyncSession = Depends(get_db)):
    """Recebe o pedido, calcula dinamicamente baseado na tabela da API mãe e debita o saldo."""
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(status_code=401, detail="Sessão expirada. Faça login novamente.")

    servicos_brutos = await obter_servicos_fornecedor()
    servico_alvo = next((s for s in servicos_brutos if int(s.get("service")) == pedido.service_id), None)
    
    if not servico_alvo:
        raise HTTPException(status_code=400, detail="Serviço indisponível no momento.")

    min_qtd = int(servico_alvo.get("min", 100))
    max_qtd = int(servico_alvo.get("max", 10000))
    if pedido.quantity < min_qtd or pedido.quantity > max_qtd:
        raise HTTPException(status_code=400, detail=f"Quantidade inválida. Permitido entre {min_qtd} e {max_qtd}.")

    preco_base = float(servico_alvo.get("rate", 0.0)) * MULTIPLICADOR_LUCRO
    custo_total = round((pedido.quantity / 1000) * preco_base, 4)

    async with db.begin():
        query = select(Usuario).where(Usuario.id == usuario_sessao.id).with_for_update()
        resultado = await db.execute(query)
        usuario_real = resultado.scalar_one_or_none()

        if not usuario_real or usuario_real.saldo < custo_total:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Custo: R$ {custo_total:.2f}")

        usuario_real.saldo = round(usuario_real.saldo - custo_total, 4)
        novo_pedido = Pedido(
            usuario_id=usuario_real.id,
            servico_id=pedido.service_id,
            link=pedido.link,
            quantidade=pedido.quantity,
            custo_total=custo_total,
            status="Processando"
        )
        db.add(novo_pedido)
        await db.flush()

    api_order_id = await despachar_ordem_provedor(pedido.service_id, pedido.link, pedido.quantity)
    
    async with db.begin():
        if api_order_id:
            novo_pedido.api_order_id = api_order_id
            novo_pedido.status = "Em Processamento"
            return {"status": "sucesso", "order_id": novo_pedido.id, "api_order_id": api_order_id}
        else:
            novo_pedido.status = "Cancelado"
            usuario_real.saldo = round(usuario_real.saldo + custo_total, 4)
            raise HTTPException(status_code=502, detail="O provedor SMM recusou o processamento. Saldo estornado.")

@router.get("/historico", status_code=status.HTTP_200_OK)
async def obter_historico_pedidos(request: Request, db: AsyncSession = Depends(get_db)):
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(status_code=401, detail="Sessão inválida.")

    query = select(Pedido).where(Pedido.usuario_id == usuario_sessao.id).order_by(Pedido.id.desc())
    resultado = await db.execute(query)
    pedidos = resultado.scalars().all()

    lista = []
    for p in pedidos:
        lista.append({
            "id": p.id,
            "servico": f"[ID {p.servico_id}] Serviço Automatizado",
            "link": p.link,
            "quantidade": f"{p.quantity:,}".replace(",", "."),
            "custo": f"R$ {p.custo_total:.2f}".replace(".", ","),
            "status": p.status
        })
    return lista
