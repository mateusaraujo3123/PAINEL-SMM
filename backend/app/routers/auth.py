from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from backend.app.database import get_db
from backend.app.models.models import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Configuração da criptografia de senha segura com Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Chave e algoritmo para a assinatura do Token JWT comercial
SECRET_KEY = "SUA_CHAVE_SECRETA_SUPER_PROTEGIDA"  # Altere ao colocar em produção
ALGORITHM = "HS256"

@router.post("/cadastro")
async def cadastrar_usuario(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Processa o registro de novos perfis individuais no banco de dados."""
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Este nome de usuário já está cadastrado.")
    
    # Cria o novo usuário com a senha criptografada e saldo da carteira zerado
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

async def obter_usuario_logado(request: Request, db: AsyncSession = Depends(get_db)):
    """Verifica o Cookie HTTP-Only de forma isolada e valida a sessão."""
    token_cookie = request.cookies.get("access_token")
    
    if not token_cookie or not token_cookie.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso não autorizado. Faça login.")
        
    # Extrai a string pura do token após o espaço "Bearer "
    partes_token = token_cookie.split(" ")
    if len(partes_token) != 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Formato de token inválido.")
    
    token_puro = partes_token[1]
    
    try:
        # Decodifica a string pura do token assinado por HS256
        payload = jwt.decode(token_puro, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
            
        # Executa a busca assíncrona na tabela usuarios
        result = await db.execute(select(Usuario).where(Usuario.username == username))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
            
        return user 
        
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada. Faça login novamente.")
