import os
import bcrypt
import mimetypes
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Corrige o cabeçalho no Linux/Railway
mimetypes.add_type("text/css", ".css", True)

# Importações do SQLAdmin e Segurança
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware

# Importações do banco e dos modelos
from backend.app.database import engine, get_db
from backend.app.models.models import Base, Usuario

app = FastAPI(title="SMM Panel Premium")

# CONFIGURAÇÃO DO GERENCIADOR DE SESSÕES OFICIAL STARLETTE
app.add_middleware(
    SessionMiddleware, 
    secret_key="CHAVE_DE_SESSAO_SUPER_SECRETA_SMM",
    session_cookie="smm_admin_session",
    same_site="lax",
    https_only=True
)

templates = Jinja2Templates(directory=".")

# ========================================================
# 🔒 TRAVA DE SEGURANÇA EXCLUSIVA DO SEU PAINEL ADMIN
# ========================================================
ADMIN_USER = "leivisonmateus2021@gmail.com"
ADMIN_PASS = "mathiasriquelme"

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == ADMIN_USER and password == ADMIN_PASS:
            request.session.update({"token": "sessao_admin_valida_smm"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if token == "sessao_admin_valida_smm":
            return True
        return False

provedor_autenticacao = AdminAuth(secret_key="CHAVE_SECRETA_ISOLADA_DO_ADMIN_SMM")
admin = Admin(app, engine, title="Painel Admin SMM", base_url="/admin", authentication_backend=provedor_autenticacao)

class UsuarioAdmin(ModelView, model=Usuario):
    column_list = [Usuario.id, Usuario.username, Usuario.saldo]
    column_searchable_list = [Usuario.username]
    form_columns = [Usuario.username, Usuario.password_hash, Usuario.saldo]
    icon = "fa fa-users"
    name = "Usuário"
    plural_name = "Usuários"
    
    async def on_model_change(self, data, model, is_created, request):
        if "password_hash" in data and data["password_hash"]:
            if not data["password_hash"].startswith("$2b$"):
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(data["password_hash"].encode('utf-8'), salt)
                data["password_hash"] = hashed.decode('utf-8')

admin.add_view(UsuarioAdmin)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 Banco de dados SMM operacional e estável na nuvem!")

# Importações dinâmicas das rotas comerciais
from backend.app.routers import auth, pedidos
app.include_router(auth.router)
app.include_router(pedidos.router)

# ========================================================
# 📦 ROTAS DIRETAS DE ATIVOS CSS (Corrigidas com o nome real do seu Github)
# ========================================================
@app.get("/login.css")
async def servir_login_css(): return FileResponse("login.css", media_type="text/css")
@app.get("/dashboard.css")
async def servir_dashboard_css(): return FileResponse("dashboard.css", media_type="text/css")
@app.get("/novo-pedido.css")
async def servir_novo_pedido_css(): return FileResponse("novo-pedido.css", media_type="text/css")
@app.get("/lista-servicos.css")
async def servir_lista_servicos_css(): return FileResponse("lista-servicos.css", media_type="text/css")
@app.get("/historico-pedidos.css")
async def servir_historico_pedidos_css(): return FileResponse("historico-pedidos.css", media_type="text/css")

# ========================================================
# 🚀 RENDERIZAÇÃO DE PÁGINAS HTML ATRAVÉS DO JINJA2
# ========================================================
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    try:
        async for session in get_db():
            from backend.app.routers.auth import obter_usuario_logado
            usuario = await obter_usuario_logado(request, db=session)
            if usuario: return RedirectResponse(url="/dashboard", status_code=303)
    except Exception: pass
    return templates.TemplateResponse(request, name="index.html", context={"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    try:
        async for session in get_db():
            from backend.app.routers.auth import obter_usuario_logado
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="dashboard.html", context={"request": request, "usuario": usuario})
    except Exception: return RedirectResponse(url="/", status_code=303)

@app.get("/novo-pedido", response_class=HTMLResponse)
async def novo_pedido_page(request: Request):
    try:
        async for session in get_db():
            from backend.app.routers.auth import obter_usuario_logado
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="novo-pedido.html", context={"request": request, "usuario": usuario})
    except Exception: return RedirectResponse(url="/", status_code=303)

@app.get("/lista-servicos", response_class=HTMLResponse)
async def servicos_page(request: Request):
    try:
        async for session in get_db():
            from backend.app.routers.auth import obter_usuario_logado
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="lista-servicos.html", context={"request": request, "usuario": usuario})
    except Exception: return RedirectResponse(url="/", status_code=303)

@app.get("/historico-pedidos", response_class=HTMLResponse)
async def historico_page(request: Request):
    try:
        async for session in get_db():
            from backend.app.routers.auth import obter_usuario_logado
            usuario = await obter_usuario_logado(request, db=session)
            return templates.TemplateResponse(request, name="historico-pedidos.html", context={"request": request, "usuario": usuario})
    except Exception: return RedirectResponse(url="/", status_code=303)
