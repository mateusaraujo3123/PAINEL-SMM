import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

# Lê as credenciais das variáveis de ambiente do Railway para total segurança
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "SEU_TOKEN_AQUI")

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank em Produção burlando o Firewall da Cloudflare."""
        referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        
        # Headers completos de alta reputação para passar direto pelo Firewall da Cloudflare
        headers = {
            "Authorization": f"Bearer {PAGBANK_TOKEN.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                # URL oficial de Produção fixa no código
                url_final = "https://pagseguro.com"
                response = await client.post(url_final, json=payload, headers=headers)
                
                # Se o banco rejeitar, trata a exibição para capturar erros de negócio do PagBank
                if response.status_code != 201:
                    print(f"!!! BANCO RECUSOU A REQUISICAO: STATUS {response.status_code} !!!")
                    if "<html" in response.text.lower():
                        raise Exception(f"Erro PagBank: Bloqueio de Firewall Cloudflare (Status {response.status_code}). Seu Token ou IP da Railway foi recusado.")
                    raise Exception(f"Erro PagBank: {response.text}")
                
                data = response.json()
                
                # Coleta estrita dos dados tratando os arrays internos conforme resposta da API v2
                lista_qr = data.get("qr_codes", [])
                if not lista_qr:
                    raise Exception("A resposta do PagBank nao trouxe a lista de qr_codes.")
                    
                qr_code_info = lista_qr[0] # Corrige o acesso ao primeiro índice do array de QR Codes
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
