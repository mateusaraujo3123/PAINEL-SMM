from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.database import get_db
from backend.app.routers.auth import obter_usuario_logado
from backend.app.models.models import Usuario, Pedido

# Injeta de forma desacoplada o motor modular do Fama Social
from backend.app.services.smm_provider import despachar_ordem_provedor

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

class PedidoSchema(BaseModel):
    service_id: int
    link: str = Field(..., min_length=5)
    quantity: int = Field(..., gte=1)

# Tabela comercial de preços de custo (Sincronizada com os valores do seu select no HTML)
# IMPORTANTE: Mapeie o ID do serviço local com o preço que você quer cobrar do seu cliente
PRECOS_PAINEL = {
    101: 12.50,  # ID do seu HTML -> R$ 12,50 por 1000 envios
    102: 8.90    # ID do seu HTML -> R$ 8,90 por 1000 envios
}

@router.post("/criar", status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    request: Request, 
    pedido: PedidoSchema, 
    db: AsyncSession = Depends(get_db)
):
    """Recebe a solicitação do front, debita com lock de segurança e despacha para o Fama Social."""
    
    # 1. VALIDAÇÃO DE SESSÃO
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Sessão inválida ou expirada. Faça login novamente."
        )

    # 2. VALIDAÇÃO COMERCIAL DE PREÇOS
    preco_por_mil = PRECOS_PAINEL.get(pedido.service_id)
    if not preco_por_mil:
        raise HTTPException(status_code=400, detail="O serviço selecionado é inválido ou não existe.")

    custo_total = round((pedido.quantity / 1000) * preco_por_mil, 4)

    # 3. VERIFICAÇÃO ATÔMICA DE SALDO (Bloqueia a linha no SQLite contra fraudes de cliques múltiplos)
    async with db.begin():
        query = select(Usuario).where(Usuario.id == usuario_sessao.id).with_for_update()
        resultado = await db.execute(query)
        usuario_real = resultado.scalar_one_or_none()

        if not usuario_real or usuario_real.saldo < custo_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Saldo insuficiente. Custo: R$ {custo_total:.2f} | Saldo disponível: R$ {usuario_sessao.saldo:.2f}."
            )

        # 4. DEBITA O SALDO IMEDIATAMENTE DA CARTEIRA DIGITAL LOCAL
        usuario_real.saldo = round(usuario_real.saldo - custo_total, 4)
        
        # 5. REGISTRA A ORDEM LOCAL COMO "PROCESSANDO"
        novo_pedido = Pedido(
            usuario_id=usuario_real.id,
            servico_id=pedido.service_id,
            link=pedido.link,
            quantidade=pedido.quantity,
            custo_total=custo_total,
            status="Processando"
        )
        db.add(novo_pedido)
        await db.flush()  # Salva temporariamente para fixar o ID local antes do disparo externo

    # 6. DISPARO PARA A API MÃE (Chama o motor isolado do Fama Social)
    # IMPORTANTE: Mapeie aqui se o ID do seu serviço do HTML for diferente do ID do provedor
    id_provedor_real = pedido.service_id  # Se forem iguais, repassa direto. Caso contrário altere aqui.
    
    api_order_id = await despachar_ordem_provedor(
        service_id=id_provedor_real,
        link=pedido.link,
        quantity=pedido.quantity
    )
    
    # 7. CONSOLIDAÇÃO TRANSACIONAL DO PROVEDOR EXTERNO
    if api_order_id:
        # Sucesso: Vincula o código de entrega gerado pelo Fama Social e altera o status
        async with db.begin():
            novo_pedido.api_order_id = api_order_id
            novo_pedido.status = "Em Processamento"
            
        return {
            "status": "sucesso",
            "order_id": novo_pedido.id,
            "api_order_id": api_order_id,
            "mensagem": "Seu pedido foi enviado e já está em processamento!"
        }
    else:
        # Estorno de Segurança: Se a API mãe recusar (Ex: fora do ar ou sem saldo), devolve o dinheiro na hora
        async with db.begin():
            novo_pedido.status = "Cancelado"
            usuario_real.saldo = round(usuario_real.saldo + custo_total, 4)
            
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail="O provedor SMM recusou a ordem ou está em manutenção. Seu saldo foi estornado."
        )


@router.get("/historico", status_code=status.HTTP_200_OK)
async def obter_historico_pedidos(request: Request, db: AsyncSession = Depends(get_db)):
    """Busca o log completo de ordens locais para alimentar a tabela do HTML."""
    usuario_sessao = await obter_usuario_logado(request, db=db)
    if not usuario_sessao:
        raise HTTPException(status_code=401, detail="Sessão inválida.")

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
