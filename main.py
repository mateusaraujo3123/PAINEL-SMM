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
async def servir_arquivos_raiz(arquivo_estatico: str, request: Request):
    # Lista estrita com os arquivos que existem na raiz do seu GitHub
    arquivos_validos = [
        "login.css", "login.js", "style.css",
        "dashboard.css", "novo-pedido.css", 
        "lista-servicos.css", "historico-pedidos.css"
    ]
    
    if arquivo_estatico in arquivos_validos and os.path.exists(arquivo_estatico):
        media_type = "text/css" if arquivo_estatico.endswith(".css") else "application/javascript"
        return FileResponse(arquivo_estatico, media_type=media_type)
    
    # Se não for um arquivo estático da lista, repassa para as rotas visuais abaixo
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

# 3. ROTAS VISUAIS DO PAINEL (Corrigidas usando o argumento explícito context=)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        if usuario:
            return RedirectResponse(url="/dashboard", status_code=303)
    except Exception:
        pass
    
    # Resolvendo o erro 500 do Jinja usando context= de forma explícita
    return templates.TemplateResponse(
        name="index.html", 
        context={"request": request}
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse(
            name="dashboard.html", 
            context={"request": request, "usuario": usuario}
        )
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse(
            name="novo-pedido.html", 
            context={"request": request, "usuario": usuario}
        )
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/lista-servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse(
            name="lista-servicos.html", 
            context={"request": request, "usuario": usuario}
        )
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/historico-pedidos", response_class=HTMLResponse)
async def historico_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario = await obter_usuario_logado(request)
        return templates.TemplateResponse(
            name="historico-pedidos.html", 
            context={"request": request, "usuario": usuario}
        )
    except Exception:
        return RedirectResponse(url="/", status_code=303)
