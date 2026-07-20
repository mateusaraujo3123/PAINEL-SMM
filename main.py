import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.app.database import engine, Base
from backend.app.routers import auth, pedidos

app = FastAPI(title="SMM Panel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router)
app.include_router(pedidos.router)

# Pega o caminho absoluto da sua raiz onde estão os arquivos soltos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Monta a própria raiz como servidora de arquivos diretamente
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="raiz")
templates = Jinja2Templates(directory=BASE_DIR)

# --- ROTAS JINJA2 CORRIGIDAS ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="dashboard.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

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
