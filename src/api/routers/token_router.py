"""
Router para gerenciamento de tokens de API.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from src.config import load_settings
import secrets
import os
import dotenv
from pathlib import Path

class TokenResponse(BaseModel):
    token: str
    message: str

class AdminCredentials(BaseModel):
    username: str = Field(..., description="Nome de usuário do administrador")
    password: str = Field(..., description="Senha do administrador")

router = APIRouter()
settings = load_settings()

# Credenciais hardcoded apenas para fins de demonstração
# Em produção, use um sistema de gerenciamento de usuários adequado
ADMIN_USERNAME = "admin"
# Em produção, armazene senhas hasheadas, não em texto puro
ADMIN_PASSWORD = "admin123"

@router.post("/generate-token", response_model=TokenResponse)
async def generate_token(credentials: AdminCredentials = Body(...)):
    """
    Gera um novo token de API. Requer credenciais de administrador.
    Este endpoint é para uso administrativo exclusivo.
    """
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )
    
    # Gera um token aleatório seguro de 32 bytes (64 caracteres em hexadecimal)
    new_token = secrets.token_hex(32)
    
    # Atualiza o arquivo .env com o novo token
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    
    # Lê o arquivo .env existente
    dotenv.load_dotenv(env_path)
    
    # Atualiza o valor do token
    os.environ["API_TOKEN"] = new_token
    
    # Escreve de volta para o arquivo .env
    dotenv.set_key(env_path, "API_TOKEN", new_token)
    
    return TokenResponse(
        token=new_token,
        message="Token gerado com sucesso. Utilize este token para autenticar chamadas à API com o header 'Authorization: Bearer {token}'."
    )
