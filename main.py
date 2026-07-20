from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.app.database import engine, Base
from backend.app.routers import auth, pedidos  # Importa os dois módulos lógicos do backend

app = FastAPI(title="SMM Panel API")

# Liberação de CORS para permitir requisições assíncronas do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas do banco de dados automaticamente na inicialização do servidor
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- INCLUSÃO DOS ROTEADORES DE INTELIGÊNCIA COMERCIAL ---
app.include_router(auth.router)     # Ativa as rotas /auth/login e /auth/cadastro
app.include_router(pedidos.router)  # Ativa a rota /api/pedidos/criar

# Configura o FastAPI para servir arquivos e ler HTMLs diretamente da raiz (.)
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

# --- ROTAS JINJA2 QUE SERVEM OS SEUS ARQUIVOS HTML ---

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
