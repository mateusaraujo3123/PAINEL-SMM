from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.app.database import engine, Base
from backend.app.routers import auth, pedidos  # Importa os módulos lógicos do seu backend

app = FastAPI(title="SMM Panel API")

# Liberação de CORS para permitir requisições assíncronas vindas do seu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas do banco de dados automaticamente assim que o servidor ligar na Railway
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- INCLUSÃO DOS ROTEADORES DE INTELIGÊNCIA COMERCIAL ---
app.include_router(auth.router)     # Ativa o sistema de login/cadastro
app.include_router(pedidos.router)  # Ativa o sistema de envio de pedidos para a API mãe

# Configura o FastAPI para servir arquivos estáticos e HTML diretamente da raiz (.)
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

# --- ROTAS JINJA2 COM SINTAXE UNIVERSAL ANTIFALHAS ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # Passagem direta e limpa aceita por todas as versões do Starlette/Jinja2
    return templates.TemplateResponse(request, "index.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(request, "dashboard.html", {"usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(request, "novo-pedido.html", {"usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(request, "lista-servicos.html", {"usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)

@app.get("/historico", response_class=HTMLResponse)
async def historico_page(request: Request):
    try:
        from backend.app.routers.auth import obter_usuario_logado
        usuario_ativo = await obter_usuario_logado(request)
        return templates.TemplateResponse(request, "historico-pedidos.html", {"usuario": usuario_ativo})
    except Exception:
        return RedirectResponse(url="/", status_code=303)
