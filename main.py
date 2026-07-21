# main.py (Na raiz do repositório)
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Importação dos roteadores internos do seu projeto
from backend.app.routers import auth, pedidos

app = FastAPI(title="SMM Panel Premium")

# Jinja2 olhando diretamente para a raiz do repositório onde estão os arquivos .html
templates = Jinja2Templates(directory=".")

# 1. Rotas da API ganham prioridade máxima de processamento
app.include_router(auth.router)
app.include_router(pedidos.router)

# 2. Rota dinâmica e segura para os arquivos estáticos (.css e .js) soltos na raiz
@app.get("/{arquivo_estatico}")
async def servir_arquivos_raiz(arquivo_estatico: str):
    # Lista estrita com os arquivos que existem na raiz do seu GitHub
    arquivos_validos = [
        "login.css", "login.js", "style.css",
        "dashboard.css", "novo-pedido.css", 
        "lista-servicos.css", "historico-pedidos.css"
    ]
    
    if arquivo_estatico in arquivos_validos and os.path.exists(arquivo_estatico):
        media_type = "text/css" if arquivo_estatico.endswith(".css") else "application/javascript"
        return FileResponse(arquivo_estatico, media_type=media_type)
    
    # Se não for um arquivo estático da lista, repassa para o FastAPI procurar outras rotas
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

# 3. ROTAS VISUAIS DO PAINEL (Sintaxe universal com request posicional)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # Passando o request como primeiro parâmetro posicional obrigatoriamente
    return templates.TemplateResponse(
        request,
        name="index.html"
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="dashboard.html"
    )

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="novo-pedido.html"
    )

@app.get("/lista-servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="lista-servicos.html"
    )

@app.get("/historico-pedidos", response_class=HTMLResponse)
async def historico_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="historico-pedidos.html"
    )
