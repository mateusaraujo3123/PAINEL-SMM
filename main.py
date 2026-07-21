# main.py (Na raiz do repositório)
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Importações do banco e dos modelos para criação automática
from backend.app.database import engine, get_db
from backend.app.models.models import Base
from backend.app.routers import auth, pedidos
from backend.app.routers.auth import obter_usuario_logado

app = FastAPI(title="SMM Panel Premium")

# Jinja2 olhando diretamente para a raiz do repositório onde estão os arquivos .html
templates = Jinja2Templates(directory=".")

# EVENTO DE STARTUP: Garante a persistência estrutural do banco local na nuvem
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 Banco de dados SMM operacional e estável na nuvem!")

# 1. Rotas da API ganham prioridade máxima de processamento
app.include_router(auth.router)
app.include_router(pedidos.router)

# 2. Rota dinâmica e segura para os arquivos estáticos (.css e .js) soltos na raiz
@app.get("/{arquivo_estatico}")
async def servir_arquivos_raiz(arquivo_estatico: str):
    # TRAVA DE SEGURANÇA: Se a rota for interna da API, não tenta ler como arquivo estático
    if arquivo_estatico.startswith("auth") or arquivo_estatico.startswith("api"):
        raise HTTPException(status_code=404, detail="Rota interna da API")

    arquivos_validos = [
        "login.css", "login.js", "style.css",
        "dashboard.css", "novo-pedido.css", 
        "lista-servicos.css", "historico-pedidos.css"
    ]
    
    if arquivo_estatico in arquivos_validos and os.path.exists(arquivo_estatico):
        media_type = "text/css" if arquivo_estatico.endswith(".css") else "application/javascript"
        return FileResponse(arquivo_estatico, media_type=media_type)
    
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

# 3. ROTAS VISUAIS DE ALTA PERFORMANCE (Protegidas por Cookie HTTP-Only)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    try:
        async for session in get_db():
            usuario = await obter_usuario_logado(request, db=session)
            if usuario:
                return RedirectResponse(url="/dashboard", status_code=303)
    except Exception:
        pass
        
    return templates.TemplateResponse(request, name="index.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        async for session in get_db():
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="dashboard.html")
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    try:
        async for session in get_db():
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="novo-pedido.html")
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/lista-servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    try:
        async for session in get_db():
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="lista-servicos.html")
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/historico-pedidos", response_class=HTMLResponse)
async def historico_page(request: Request):
    try:
        async for session in get_db():
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="historico-pedidos.html")
    except Exception:
        return RedirectResponse(url="/", status_code=303)
