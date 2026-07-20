from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.app.routers import auth, pedidos  # Atualizado aqui
from backend.app.database import engine, Base
from backend.app.routers import auth  # Puxa o seu sistema de login feito na pasta interna

app = FastAPI(title="SMM Panel API")

# Mantém a liberação de acesso que você configurou para os scripts JS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria a tabela de usuários assíncrona assim que o painel ligar
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Inclui as rotas lógicas de autenticação (/auth/login e /auth/cadastro)
app.include_router(auth.router)

# Configura o FastAPI para ler os seus CSS/JS e HTMLs que estão soltos na raiz (.)
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

# --- ROTAS DE RENDERIZAÇÃO PRESTES A USAR NO JINJA2 ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve a tela de login/cadastro premium."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve o painel principal com menu lateral."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    """Serve o formulário de novos pedidos."""
    return templates.TemplateResponse("novo-pedido.html", {"request": request})

@app.get("/servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    """Serve a tabela comercial com filtro."""
    return templates.TemplateResponse("lista-servicos.html", {"request": request})

@app.get("/historico", response_class=HTMLResponse)
async def historico_page(request: Request):
    """Serve o painel com logs de status."""
    return templates.TemplateResponse("historico-pedidos.html", {"request": request})
