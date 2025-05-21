from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    fastmcp_server_host: str = "localhost"
    fastmcp_server_port: int = 8000
    log_level: str = "info"
    gemini_api_key: str = "sua_chave_api_gemini"
    gemini_model: str = "gemini-2.5-flash-preview-04-17"
    mcp_server_url: str = "http://localhost:8000"
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    
    # Configurações JWT - mantidas para evitar erro no middleware de sessões
    jwt_secret_key: str = "chave_secreta_temporaria_deve_ser_substituida"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env")
    )

def load_settings() -> Settings:
    return Settings()
