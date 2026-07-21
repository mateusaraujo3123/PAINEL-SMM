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

# 1. Rotas da API ganham prioridade máxima absoluta de processamento
app.include_router(auth.router)
app.include_router(pedidos.router)

# 2. ROTAS ESTÁTICAS INDIVIDUAIS: Mapeamento explícito para eliminar o conflito de rotas da API
@app.get("/login.css")
async def servir_login_css():
    return FileResponse("login.css", media_type="text/css")

@app.get("/dashboard.css")
async def servir_dashboard_css():
    return FileResponse("dashboard.css", media_type="text/css")

@app.get("/novo-pedido.css")
async def servir_novo_pedido_css():
    return FileResponse("novo-pedido.css", media_type="text/css")

@app.get("/lista-servicos.css")
async def servir_lista_servicos_css():
    return FileResponse("lista-servicos.css", media_type="text/css")

@app.get("/historico-pedidos.css")
async def servir_historico_pedidos_css():
    return FileResponse("historico-pedidos.css", media_type="text/css")

@app.get("/style.css")
async def servir_style_css():
    if os.path.exists("style.css"):
        return FileResponse("style.css", media_type="text/css")
    raise HTTPException(status_code=404, detail="Style não encontrado")

@app.get("/login.js")
async def servir_login_js():
    if os.path.exists("login.js"):
        return FileResponse("login.js", media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Script não encontrado")


# 3. ROTAS VISUAIS DE ATENDIMENTO (Protegidas por Cookie HTTP-Only)

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
