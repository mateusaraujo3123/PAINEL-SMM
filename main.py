# main.py (Na raiz do repositório)
from fastapi import FastAPI, Request, Depends
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="SMM Panel Premium")

# Jinja configurado diretamente na raiz do projeto
templates = Jinja2Templates(directory=".")

# --- ROTA DINÂMICA PARA ARQUIVOS ESTÁTICOS SOLTOS NA RAIZ ---
# Impede que você tenha que criar uma rota manual para cada arquivo .css ou .js
@app.get("/{arquivo_estatico}")
async def servir_arquivos_raiz(arquivo_estatico: str):
    extensoes_permitidas = [".css", ".js", ".png", ".jpg", ".svg", ".ico"]
    extensao = os.path.splitext(arquivo_estatico)[1]
    
    if extensao in extensoes_permitidas and os.path.exists(arquivo_estatico):
        media_types = {
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon"
        }
        return FileResponse(arquivo_estatico, media_type=media_types.get(extensao, "text/plain"))
    
    # Se não for um arquivo válido, deixa o FastAPI repassar para as rotas visuais
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

# --- ROTAS VISUAIS DE ATENDIMENTO (Exemplo de proteção de estado) ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    # Seu bloco try/except com obter_usuario_logado(request) entra aqui
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="novo-pedido.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="lista-servicos.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/historico", response_class=HTMLResponse)
async def historico_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="historico-pedidos.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)
