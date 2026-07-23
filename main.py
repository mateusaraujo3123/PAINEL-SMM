import os
import bcrypt
import mimetypes
import base64
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from efi import EfiPay

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

# Importações dinâmicas das rotas comerciais
from backend.app.routers import auth, pedidos
app.include_router(auth.router)
app.include_router(pedidos.router)

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
# 💳 INTEGRAÇÃO SISTEMA DE PAGAMENTO VIA API PIX (EFÍ BANK)
# ========================================================
def obter_client_efi():
    """Decodifica temporariamente o certificado da memória para a SDK da Efí"""
    cert_base64 = os.getenv("EFI_CERTIFICADO_BASE64")
    if not cert_base64:
        raise HTTPException(status_code=500, detail="Certificado Efí não configurado nas variáveis.")
    
    cert_path = "/tmp/certificado_efi.p12"
    with open(cert_path, "wb") as f:
        f.write(base64.b64decode(cert_base64))
        
    efi_config = {
        "client_id": os.getenv("EFI_CLIENT_ID"),
        "client_secret": os.getenv("EFI_CLIENT_SECRET"),
        "sandbox": False,
        "certificate": cert_path
    }
    return EfiPay(efi_config)

@app.get("/pagamento/gerar-pix", response_class=HTMLResponse)
async def gerar_pagamento_pix(request: Request, valor: float):
    if valor <= 0:
        raise HTTPException(status_code=400, detail="O valor precisa ser maior que zero.")
    
    try:
        # Inicia a API da Efí de forma segura
        efi = obter_client_efi()
        valor_formatado = f"{valor:.2f}"
        
        # 1. Monta os parâmetros do Pix
        body = {
            "calendario": {"expiracao": 3600},
            "valor": {"original": valor_formatado},
            "chave": os.getenv("EFI_CHAVE_PIX")
        }
        
        # 2. Cria a cobrança imediata na Efí
        cob_response = efi.pix_create_immediate_charge(body=body)
        loc_id = cob_response.get("loc", {}).get("id")
        
        # 3. Gera a linha Copia e Cola e o QR Code em Imagem
        qrcode_response = efi.pix_generate_qrcode(params={"id": str(loc_id)})
        pix_copia_e_cola = qrcode_response.get("qrcode")
        qr_code_base64 = qrcode_response.get("imagemQrcode")
        
        # 4. Envia os dados para renderizar na tela pagamento.html
        return templates.TemplateResponse(request, name="pagamento.html", context={
            "request": request,
            "valor": valor_formatado,
            "pix_copia_e_cola": pix_copia_e_cola,
            "qr_code_base64": qr_code_base64
        })
        
    except Exception as e:
        print(f"❌ Erro crítico na API Efí Pix: {str(e)}")
        raise HTTPException(status_code=500, detail="Não foi possível gerar seu Pix. Tente novamente.")
