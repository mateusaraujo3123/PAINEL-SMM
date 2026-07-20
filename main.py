from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
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

# --- ROTAS JINJA2 QUE SERVEM OS SEUS ARQUIVOS HTML COM TRAVA DE SEGURANÇA ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página pública de Login e Cadastro."""
    # SINTAXE CORRIGIDA: Passando explicitamente como name e context
    return templates.TemplateResponse(name="index.html", context={"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Painel principal protegido por sessão."""
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="dashboard.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    """Formulário de pedidos protegido por sessão."""
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="novo-pedido.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    """Tabela comercial de serviços protegida por sessão."""
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="lista-servicos.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/historico", response_class=HTMLResponse)
async def historico_page(request: Request):
    """Logs de pedidos protegidos por sessão."""
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(name="historico-pedidos.html", context={"request": request, "usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)
