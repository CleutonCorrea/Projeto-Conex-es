"""
Utilitários de autenticação para rotas da API.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config import load_settings
import secrets
import hmac

# Configuração do bearer token
security = HTTPBearer()
settings = load_settings()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica se o token fornecido é válido.
    
    Args:
        credentials: Credenciais obtidas da requisição HTTP
        
    Returns:
        bool: True se o token for válido
        
    Raises:
        HTTPException: Se o token for inválido ou não fornecido
    """
    # Comparação segura contra timing attacks
    is_valid = hmac.compare_digest(credentials.credentials, settings.api_token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return True
