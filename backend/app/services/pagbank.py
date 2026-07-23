import httpx
import uuid

PAGBANK_TOKEN = "SEU_TOKEN_AQUI"
# Use https://sandbox.api.pagseguro.com para testes
PAGBANK_URL = "https://api.pagseguro.com" 

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank e retorna as chaves do QR Code."""
        referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        
        headers = {
            "Authorization": f"Bearer {PAGBANK_TOKEN}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

        # Formata o valor para centavos exigido pela API Order do PagBank
        valor_centavos = int(valor * 100)

        payload = {
            "reference_id": referencia_internA,
            "customer": {
                "name": username,
                "email": f"{username}@smm.com" # Email placeholder ou use do usuário real
            },
            "qr_codes": [
                {
                    "amount": {
                        "value": valor_centavos
                    },
                    "expiration_date": (httpx.utils.now() + 3600).strftime("%Y-%m-%dT%H:%M:%S-03:00") # Expira em 1 hora
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{PAGBANK_URL}/orders", json=payload, headers=headers)
            
            if response.status_code != 201:
                raise Exception(f"Erro PagBank: {response.text}")
            
            data = response.json()
            
            # Extrai os dados do QR code dinâmico gerado
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
