# main.py (Na raiz do repositório)
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Importe seus roteadores originais
from backend.app.routers import auth, pedidos

app = FastAPI(title="SMM Panel Premium")

# Jinja2 olhando direto para a raiz do repositório
templates = Jinja2Templates(directory=".")

# 1. Primeiro registramos as rotas da API para que tenham prioridade máxima
app.include_router(auth.router)
app.include_router(pedidos.router)

# 2. Rota explícita e ultra segura para os arquivos estáticos soltos na raiz
@app.get("/{arquivo_estatico}")
async def servir_arquivos_raiz(arquivo_estatico: str, request: Request):
    # Lista restrita apenas aos arquivos reais mapeados no seu GitHub
    arquivos_validos = [
        "login.css", "login.js", "style.css",
        "dashboard.css", "novo-pedido.css", 
        "lista-servicos.css", "historico-pedidos.css"
    ]
    
    if arquivo_estatico in arquivos_validos and os.path.exists(arquivo_estatico):
        media_type = "text/css" if arquivo_estatico.endswith(".css") else "application/javascript"
        return FileResponse(arquivo_estatico, media_type=media_type)
    
    # Se o usuário digitou uma rota visual na URL (ex: /dashboard, /novo-pedido)
    # o FastAPI não vai achar o arquivo na lista acima e processará as rotas HTML abaixo
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

# 3. ROTAS VISUAIS DO PAINEL (Garantindo a presença obrigatória do request)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    try:
        # Importe aqui a sua função de validação de cookie HTTP-Only
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        if usuario:
            return RedirectResponse(url="/dashboard", status_code=303)
    except Exception:
        pass
    
    # IMPORTANTE: Sempre passe o request no contexto para evitar Erro 500
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse("dashboard.html", {"request": request, "usuario": usuario})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse("novo-pedido.html", {"request": request, "usuario": usuario})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/lista-servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse("lista-servicos.html", {"request": request, "usuario": usuario})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/historico-pedidos", response_class=HTMLResponse)
async def historico_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse("historico-pedidos.html", {"request": request, "usuario": usuario})
    except Exception:
        return RedirectResponse(url="/", status_code=303)
