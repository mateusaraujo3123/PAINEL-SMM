import httpx
import logging

logger = logging.getLogger("smm_provider")

# =========================================================================
# ⚙️ PAINEL DE CONFIGURAÇÃO DO FORNECEDOR (MUDE AQUI PARA TROCAR DE MÃE)
# =========================================================================
# Sempre que precisar trocar de fornecedor, altere apenas os dados abaixo:
FORNECEDOR_API_URL = "https://painelfamasocial.com.br"  # URL do Painel Fama Social
FORNECEDOR_API_KEY = "SUA_CHAVE_DA_API_MAE"  # Substitua pelo seu Token gerado na aba API do painel deles
# =========================================================================

async def despachar_ordem_provedor(service_id: int, link: str, quantity: int) -> int | None:
    """
    Envia a ordem de compra via método POST para o fornecedor configurado no painel acima.
    
    Retorna:
        int: O número da ordem (ID) gerado com sucesso no provedor principal.
        None: Em caso de falha de conexão, falta de saldo na API mãe ou parâmetros inválidos.
    """
    # Payload estruturado no padrão estrito da documentação do Fama Social
    payload = {
        "key": FORNECEDOR_API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    }
    
    try:
        # Timeout seguro de 12 segundos para não congelar o banco local
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(FORNECEDOR_API_URL, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Se o Fama Social aprovar o envio, ele responde com {"order": 23501}
                if "order" in data and data["order"]:
                    return int(data["order"])
                
                # Se o Fama Social recusar o envio por algum erro interno ou falta de saldo
                if "error" in data:
                    logger.error(f"🚨 Provedor recusou os dados. Motivo: {data['error']}")
            else:
                logger.error(f"🚨 Servidor do provedor retornou HTTP Status inválido: {response.status_code}")
                
    except httpx.RequestError as exc:
        logger.error(f"🚨 Falha física de rede/conexão com o provedor: {exc}")
    except Exception as e:
        logger.error(f"🚨 Erro imprevisto no tratamento da API Mãe: {str(e)}")
        
    return None
