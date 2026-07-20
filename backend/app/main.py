from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.app.database import engine, Base
from backend.app.routers import auth  # Importa o módulo de login/cadastro

app = FastAPI(title="Painel SMM Comercial - Alta Performance")

# Cria as tabelas do banco de dados automaticamente na inicialização
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Inclui as rotas comerciais de Autenticação (/auth/login e /auth/cadastro)
app.include_router(auth.router)

# Configuração de arquivos estáticos e Jinja2
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rotas de renderização das suas páginas HTML
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    return templates.TemplateResponse("novo-pedido.html", {"request": request})

@app.get("/servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    return templates.TemplateResponse("lista-servicos.html", {"request": request})

@app.get("/historico", response_class=HTMLResponse)
async def historico_page(request: Request):
    return templates.TemplateResponse("historico-pedidos.html", {"request": request})
