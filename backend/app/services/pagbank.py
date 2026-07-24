import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "")

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank tratando cenários de ausência de arranjo Pix na conta."""
        try:
            referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
            token_limpo = str(PAGBANK_TOKEN).replace("\n", "").replace("\r", "").strip()
            
            if not token_limpo or token_limpo == "SEU_TOKEN_AQUI":
                raise Exception("O PAGBANK_TOKEN nao foi configurado na Railway.")

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
                    raise Exception(f"Banco recusou (Status {response.status_code}): {response.text}")
                
                data = response.json()
                lista_qr = data.get("qr_codes", [])
                
                # VALIDAÇÃO SEGURA: Impede o erro de índice caso a conta não tenha Pix configurado
                if not lista_qr or len(lista_qr) == 0:
                    raise Exception("A conta vinculada a este Token nao possui chaves Pix ativas ou homologadas no PagBank.")
                    
                qr_code_info = lista_qr[0]
                copy_paste = qr_code_info.get("text", "")
                
                qr_code_img = ""
                for link in qr_code_info.get("links", []):
                    if link.get("rel") == "QRCODE.PNG":
                        qr_code_img = link.get("href")
                        break

                return {
                    "pagbank_id": data.get("id"),
                    "referencia": referencia_internA,
                    "qrcode_text": copy_paste,
                    "qrcode_img": qr_code_img
                }

        except Exception as erro_geral:
            mensagem_formatada = str(erro_geral)
            print(f"!!! ERRO COMPLETO DETECTADO: {mensagem_formatada} !!!")
            raise Exception(mensagem_formatada)
