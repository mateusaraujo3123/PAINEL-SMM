from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SMM Panel API")

# 🔴 ISSO É NOVO: Libera o acesso para o seu HTML enviar dados à API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite qualquer origem temporariamente para testes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PedidoSMM(BaseModel):
    servico_id: int
    link_rede_social: str
    quantidade: int

@app.post("/pedidos", status_code=status.HTTP_201_CREATED)
async def criar_pedido(pedido: PedidoSMM):
    print(f"Pedido recebido no backend! {pedido}") # Aparece no seu terminal
    return {
        "status": "sucesso", 
        "mensagem": "Pedido enviado para processamento",
        "detalhes": pedido
    }
