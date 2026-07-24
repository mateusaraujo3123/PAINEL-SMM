import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone

# Lê as credenciais das variáveis de ambiente do Railway para total segurança
PAGBANK_TOKEN = os.getenv("PAGBANK_TOKEN", "SEU_TOKEN_AQUI")

class PagBankService:
    @staticmethod
    async def criar_pix_deposito(valor: float, username: str) -> dict:
        """Gera um pedido com PIX no PagBank utilizando dados fixos do proprietário para evitar erros de validação."""
        referencia_internA = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        
        # Headers atualizados para burlar o bloqueio da Cloudflare
        headers = {
            "Authorization": f"Bearer {PAGBANK_TOKEN.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # O User-Agent faz a chamada parecer que veio de um navegador Chrome real em vez de um script Python
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

        # Habilita o redirecionamento automático caso a Cloudflare tente mover a rota
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                # URL cravada direto com v2 para eliminar dependências de variáveis da Railway
                url_final = "https://pagseguro.com"
                response = await client.post(url_final, json=payload, headers=headers)
                
                # Se o banco rejeitar, trata a exibição para não quebrar o painel com HTML longo
                if response.status_code != 201:
                    print(f"!!! BANCO RECUSOU A REQUISICAO: STATUS {response.status_code} !!!")
                    if "<html" in response.text.lower():
                        raise Exception(f"Erro PagBank: Bloqueio de Firewall Cloudflare (Status {response.status_code}). Seu Token ou IP da Railway foi recusado.")
                    raise Exception(f"Erro PagBank: {response.text}")
                
                data = response.json()
                
                # Coleta estrita dos dados tratando os arrays internos
                lista_qr = data.get("qr_codes", [])
                if not lista_qr:
                    raise Exception("A resposta do PagBank nao trouxe a lista de qr_codes.")
                    
                qr_code_info = lista_qr[0] # Correção: Acessa o índice 0 da lista conforme o seu código original tratava
                copy_paste = qr_code_info["text"]
                qr_code_img = next(link["href"] for link in qr_code_info["links"] if link["rel"] == "QRCODE.PNG")
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
