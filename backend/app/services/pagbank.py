import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

# Coleta o token tratando caso ele não exista na Railway
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "")

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank imprimindo qualquer erro de sintaxe interno."""
        try:
            referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
            
            # Limpa o token de forma segura sem estourar erro caso esteja vazio
            token_string = str(PAGBANK_TOKEN)
            token_limpo = token_string.replace("\n", "").replace("\r", "").strip()
            
            if not token_limpo or token_limpo == "SEU_TOKEN_AQUI":
                raise Exception("O PAGBANK_TOKEN nao foi configurado ou esta vazio na Railway.")

            headers = {
                "Authorization": f"Bearer {token_limpo}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            valor_centavos = int(valor * 100)

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

            proxy_url = "http://31.59.20"

            async with httpx.AsyncClient(proxy=proxy_url, follow_redirects=True, timeout=30.0) as client:
                url_final = "https://pagseguro.com"
                response = await client.post(url_final, json=payload, headers=headers)
                
                if response.status_code != 201:
                    detalhe_erro = response.text if response.text.strip() else f"Status {response.status_code} vazio."
                    raise Exception(f"Erro PagBank ({response.status_code}): {detalhe_erro}")
                
                data = response.json()
                
                lista_qr = data.get("qr_codes", [])
                if not lista_qr:
                    raise Exception("A resposta do PagBank nao trouxe a lista de qr_codes.")
                    
                qr_code_info = lista_qr
                copy_paste = qr_code_info["text"]
                
                qr_code_img = ""
                for link in qr_code_info.get("links", []):
                    if link.get("rel") == "QRCODE.PNG":
                        qr_code_img = link.get("href")
                        break

                return {
                    "pagbank_id": data["id"],
                    "referencia": referencia_internA,
                    "qrcode_text": copy_paste,
                    "qrcode_img": qr_code_img
                }

        except Exception as erro_geral:
            # Força o Python a cuspir a linha e o motivo exato de ter parado
            mensagem_erro = f"FALHA INTERNA: {str(erro_geral)}"
            print(f"!!! ERRO COMPLETO DETECTADO: {mensagem_erro} !!!")
            raise Exception(mensagem_erro)
