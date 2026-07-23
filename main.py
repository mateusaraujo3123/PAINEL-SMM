import sys
import os
# Adiciona a pasta backend ao sistema de caminhos do Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
import os
import bcrypt
import mimetypes
import base64
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Força o Linux e o Railway a entregarem os estilos como text/css
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

# Importações dinâmicas das rotas comerciais (Incluindo Pagamentos)
from backend.app.routers import auth, pedidos, pagamentos
app.include_router(auth.router)
app.include_router(pedidos.router)
app.include_router(pagamentos.router) # Injeta o novo router do PagBank de forma limpa

# ========================================================
# 📦 ROTAS DIRETAS DE ATIVOS CSS (Sincronizadas com o seu Github)
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

# ========================================================
# 🚀 RENDERIZAÇÃO DA PÁGINA DE PAGAMENTO (PAGBANK JINJA2)
# ========================================================
@app.get("/pagamento", response_class=HTMLResponse)
async def visualizar_pagamento(request: Request, referencia: str):
    """Busca os dados do Pix dinâmico gerado e renderiza na interface do cliente"""
    if not referencia:
        raise HTTPException(status_code=400, detail="Referência inválida.")
        
    try:
        async for session in get_db():
            from backend.app.models.models import Deposito
            from sqlalchemy.future import select
            
            # Busca o depósito correspondente no SQLite local
            stmt = select(Deposito).where(Deposito.referencia == referencia)
            resultado = await session.execute(stmt)
            deposito = resultado.scalar_one_or_none()
            
            if not deposito:
                raise HTTPException(status_code=404, detail="Depósito não localizado.")
                
            # Como salvamos apenas os IDs na criação, geramos as variáveis para renderização
            # NOTA: Adapte as chaves se você guardou o texto direto no modelo
            from backend.app.services.pagbank import PAGBANK_URL, PAGBANK_TOKEN
            import httpx
            
            # Consulta os dados em tempo real no PagBank para obter os hashes visuais com segurança
            url = f"{PAGBANK_URL}/orders/{deposito.pagbank_id}"
            headers = {"Authorization": f"Bearer {PAGBANK_TOKEN}", "accept": "application/json"}
            
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    qr_code_info = data["qr_codes"][0]
                    qrcode_text = qr_code_info["text"]
                    qrcode_img = next(link["href"] for link in qr_code_info["links"] if link["rel"] == "QRCODE.PNG")
                    
                    return templates.TemplateResponse(
                        request, 
                        name="pagamento.html", 
                        context={
                            "request": request,
                            "valor": f"{deposito.valor:.2f}",
                            "qrcode": qrcode_text,
                            "qrcode_img": qrcode_img,
                            "referencia": referencia
                        }
                    )
    except HTTPException as he: raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno de renderização: {str(e)}")
