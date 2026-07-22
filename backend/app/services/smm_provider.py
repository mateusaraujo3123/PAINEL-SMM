import httpx
import logging

logger = logging.getLogger("smm_provider")

async def enviar_pedido_fornecedor(api_url: str, api_key: str, service_id: int, link: str, quantidade: int) -> int | None:
    """
    Envia a ordem diretamente para a API do seu fornecedor SMM.
    Retorna o ID da ordem no fornecedor ou None se houver falha.
    """
    payload = {
        "key": api_key,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantidade
    }
    
    try:
        # Timeout de 12 segundos para não travar a requisição do cliente se o fornecedor demorar
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(api_url, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "order" in data:
                    return int(data["order"])
                else:
                    logger.error(f"Erro na resposta do fornecedor SMM: {data.get('error', 'Sem detalhe')}")
            else:
                logger.error(f"Fornecedor SMM retornou HTTP Status {response.status_code}")
                
    except Exception as e:
        logger.error(f"Falha de conexão física com o fornecedor SMM: {str(e)}")
        
    return None
