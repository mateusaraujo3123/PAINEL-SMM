from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from backend.app.database import get_db
from backend.app.models.models import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Configuração da criptografia de senha segura
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Chave e algoritmo para o token JWT comercial
SECRET_KEY = "SUA_CHAVE_SECRETA_SUPER_PROTEGIDA"  # Altere ao colocar em produção
ALGORITHM = "HS256"

@router.post("/cadastro")
async def cadastrar_usuario(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Processa o registro de novos perfis individuais no banco de dados."""
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Este nome de usuário já está cadastrado.")
    
    # Cria o novo usuário com a senha criptografada e saldo zerado
    novo_user = Usuario(username=username, password_hash=pwd_context.hash(password))
    db.add(novo_user)
    await db.commit()
    return {"status": "sucesso", "mensagem": "Sua conta foi criada com sucesso!"}

@router.post("/login")
async def login_usuario(response: Response, username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Valida o login e insere o Token JWT em um cookie seguro HTTP-only."""
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    user = result.scalars().first()
    
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
    
    # Define o tempo de expiração do login (12 horas padrão comercial)
    tempo_expiracao = datetime.now(timezone.utc) + timedelta(hours=12)
    token = jwt.encode({"sub": user.username, "exp": tempo_expiracao}, SECRET_KEY, algorithm=ALGORITHM)
    
    # Armazena o token em Cookie HTTP-Only para mitigar ataques XSS no frontend
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, samesite="lax")
    return {"status": "sucesso", "redirecionar": "/dashboard"}
