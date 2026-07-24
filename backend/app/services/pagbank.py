import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

# Lê as credenciais das variáveis de ambiente com tratamento de string limpa
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "").strip()

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank tratando retornos vazios do servidor de produção."""
        referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        
        # Garante que o Token não vá com quebras de linha ou espaços
        token_limpo = PAGBANK_TOKEN.replace("\n", "").replace("\r", "").strip()
        
        headers = {
            "Authorization": f"Bearer {token_limpo}",
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

        # Proxy residencial do Webshare fixado para contornar o bloqueio de IP da Railway
        proxy_url = "http://31.59.20"

        async with httpx.AsyncClient(proxy=proxy_url, follow_redirects=True, timeout=30.0) as client:
            try:
                url_final = "https://pagseguro.com"
                response = await client.post(url_final, json=payload, headers=headers)
                
                # Tratamento robusto para capturar a rejeição de credenciais do banco
                if response.status_code != 201:
                    print(f"!!! BANCO RECUSOU A REQUISICAO: STATUS CODE {response.status_code} !!!")
                    detalhe_erro = response.text if response.text.strip() else "Resposta vazia do servidor."
                    
                    if response.status_code == 401:
                        raise Exception(f"Erro PagBank (401): Seu Token de produção é inválido ou expirou. Revise na Railway.")
                    if response.status_code == 403:
                        raise Exception(f"Erro PagBank (403): Conta sem permissão para Pix via API. Requer homologação no painel do banco.")
                    
                    raise Exception(f"Erro PagBank (Status {response.status_code}): {detalhe_erro}")
                
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
                # Imprime o erro completo com detalhes no log da Railway para diagnóstico rápido
                print(f"!!! ERRO COMPLETO DETECTADO: {str(erro_interno)} !!!")
                raise erro_interno
