import httpx
import logging

logger = logging.getLogger("smm_provider")

# =========================================================================
# ⚙️ PAINEL DE CONFIGURAÇÃO DO FORNECEDOR (MUDE AQUI PARA TROCAR DE MÃE)
# =========================================================================
# Sempre que precisar trocar de fornecedor SMM, altere apenas estes dados:
FORNECEDOR_API_URL = "https://painelfamasocial.com.br/api/v2"  # Endpoint Fama Social
FORNECEDOR_API_KEY = "SUA_CHAVE_DA_API_MAE"                  # Insira seu token de API real aqui
# =========================================================================

async def obter_servicos_fornecedor() -> list:
    """Busca o catálogo completo de serviços atualizados direto do fornecedor via POST."""
    payload = {
        "key": FORNECEDOR_API_KEY,
        "action": "services"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(FORNECEDOR_API_URL, data=payload)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"🚨 Erro ao listar serviços do fornecedor: {str(e)}")
    return []

async def despachar_ordem_provedor(service_id: int, link: str, quantity: int) -> int | None:
    """Envia uma nova ordem de compra para a API do fornecedor e retorna o ID da ordem."""
    payload = {
        "key": FORNECEDOR_API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(FORNECEDOR_API_URL, data=payload)
            if response.status_code == 200:
                data = response.json()
                if "order" in data and data["order"]:
                    return int(data["order"])
                if "error" in data:
                    logger.error(f"🚨 Fornecedor recusou o pedido: {data['error']}")
    except Exception as e:
        logger.error(f"🚨 Falha física de rede com o fornecedor SMM: {str(e)}")
    return None
