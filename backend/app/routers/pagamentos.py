from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# CORREÇÃO DE IMPORTS (Adicionando o prefixo backend.)
from backend.app.database import get_db
from backend.app.models.models import Deposito, Usuario
from backend.app.services.pagbank import PagBankService
from backend.app.routers.auth import obter_usuario_logado


router = APIRouter(prefix="/api/pagamentos", tags=["Pagamentos"])

@router.post("/adicionar-saldo")
async def iniciar_deposito(payload: dict, db: AsyncSession = Depends(get_db), usuario_atual = Depends(obter_usuario_logado)):
    valor = float(payload.get("valor", 0))
    if valor < 10.0: # Regra de depósito mínimo
        raise HTTPException(status_code=400, detail="Depósito mínimo é de R$ 10,00")

    try:
        dados_pix = await PagBankService.criar_pix_deposito(valor, usuario_atual.username)
        
        # Registra a transação PENDENTE no banco persistente
        novo_deposito = Deposito(
            usuario_id=usuario_atual.id,
            pagbank_id=dados_pix["pagbank_id"],
            referencia=dados_pix["referencia"],
            valor=valor,
            status="PENDENTE"
        )
        db.add(novo_deposito)
        await db.commit()

        return {
            "sucesso": True,
            "qrcode": dados_pix["qrcode_text"],
            "qrcode_img": dados_pix["qrcode_img"],
            "referencia": dados_pix["referencia"]
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def webhook_pagbank(request: Request, db: AsyncSession = Depends(get_db)):
    """Recebe a notificação oficial do PagBank e adiciona o saldo na conta"""
    payload = await request.json()
    
    # Valida se o evento representa uma transação paga
    status_pagbank = payload.get("status")
    referencia = payload.get("reference_id")
    
    if status_pagbank == "PAID" and referencia:
        # Busca o depósito correspondente que ainda está pendente
        stmt = select(Deposito).where(Deposito.referencia == referencia, Deposito.status == "PENDENTE")
        resultado = await db.execute(stmt)
        deposito = resultado.scalar_one_or_none()
        
        if deposito:
            # Altera status do depósito
            deposito.status = "PAGO"
            
            # Localiza o usuário e credita o saldo de forma atômica
            stmt_user = select(Usuario).where(Usuario.id == deposito.usuario_id)
            res_user = await db.execute(stmt_user)
            usuario = res_user.scalar_one_or_none()
            
            if usuario:
                usuario.saldo += deposito.valor
                await db.commit()
                return {"status": "sucesso", "mensagem": "Saldo creditado"}
                
    return {"status": "ignorado"}
