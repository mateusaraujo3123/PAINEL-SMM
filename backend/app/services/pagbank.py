import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

# Lê as credenciais das variáveis de ambiente do Railway para total segurança
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "SEU_TOKEN_AQUI")

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank em Produção corrigindo o parâmetro proxy do HTTPX."""
        referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        
        headers = {
            "Authorization": f"Bearer {PAGBANK_TOKEN.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Formata o valor para centavos exigido pela API Order do PagBank
        valor_centavos = int(valor * 100)

        # Define a expiração exata usando UTC-3 (Horário de Brasília) exigido pelo PagBank
        fuso_brasil = timezone(timedelta(hours=-3))
        data_expiracao = (datetime.now(fuso_brasil) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

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

        # Configura o parâmetro de acordo com o httpx atual (usa 'proxy' no singular em vez de 'proxies')
        proxy_url = os.getenv("PROXY_URL_RAILWAY", None)

        async with httpx.AsyncClient(proxy=proxy_url, follow_redirects=True, timeout=30.0) as client:
            try:
                url_final = "https://pagseguro.com"
                response = await client.post(url_final, json=payload, headers=headers)
                
                # Se a Cloudflare retornar 200 mas for o desafio em HTML
                if response.status_code == 200 and "<html" in response.text.lower():
                    raise Exception("A Cloudflare barrou a chamada direta por IP de hospedagem. Adicione uma PROXY_URL_RAILWAY válida.")

                if response.status_code != 201:
                    print(f"!!! BANCO RECUSOU A REQUISICAO: STATUS {response.status_code} !!!")
                    raise Exception(f"Erro PagBank: {response.text}")
                
                data = response.json()
                
                lista_qr = data.get("qr_codes", [])
                if not lista_qr:
                    raise Exception("A resposta do PagBank nao trouxe a lista de qr_codes.")
                    
                qr_code_info = lista_qr[0]
                copy_paste = qr_code_info["text"]
                
                qr_code_img = None
                for link in qr_code_info.get("links", []):
                    if link.get("rel") == "QRCODE.PNG":
                        qr_code_img = link.get("href")
                        break
                
                if not qr_code_img:
                    qr_code_img = ""

                pagbank_id = data["id"]

                return {
                    "pagbank_id": pagbank_id,
                    "referencia": referencia_internA,
                    "qrcode_text": copy_paste,
                    "qrcode_img": qr_code_img
                }
            except Exception as erro_interno:
                print(f"!!! ERRO NA REQUISICAO PIX: {str(erro_interno)} !!!")
                raise erro_interno
