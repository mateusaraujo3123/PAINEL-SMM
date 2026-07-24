import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

# Lê as credenciais   das variáveis de ambiente do Railway para total segurança
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "SEU_TOKEN_AQUI")
PAGBANK_URL = os.getenv("PAGBANK_URL", "https://pagseguro.com")

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank utilizando dados fixos do proprietário para evitar erros de validação."""
        referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        
        headers = {
            "Authorization": f"Bearer {PAGBANK_TOKEN}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

        # Formata o valor para centavos exigido pela API Order do PagBank
        valor_centavos = int(valor * 100)

        # Define a expiração exata usando UTC-3 (Horário de Brasília) exigido pelo PagBank
        fuso_brasil = timezone(timedelta(hours=-3))
        data_expiracao = (datetime.now(fuso_brasil) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

        # Dados estruturados e validados do titular para envio limpo à API do banco
        payload = {
            "reference_id": referencia_internA,
            "customer": {
                "name": "Leivison Mateus De Araujo Sobral",
                "email": "Leivisonmateus2021@gmail.com",
                "tax_id": "07428300479"
            },
            "qr_codes": [
                {
                    "amount": {
                        "value": valor_centavos
                    },
                    "expiration_date": data_expiracao
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{PAGBANK_URL}/orders", json=payload, headers=headers)
            
            if response.status_code != 201:
                raise Exception(f"Erro PagBank: {response.text}")
            
            data = response.json()
            
            # Correção sintática estrita: Acessa o primeiro índice [0] da lista retornada
            qr_code_info = data["qr_codes"][0]
            copy_paste = qr_code_info["text"]
            qr_code_img = next(link["href"] for link in qr_code_info["links"] if link["rel"] == "QRCODE.PNG")
            pagbank_id = data["id"]

            return {
                "pagbank_id": pagbank_id,
                "referencia": referencia_internA,
                "qrcode_text": copy_paste,
                "qrcode_img": qr_code_img
            }
