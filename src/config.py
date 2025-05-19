from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    fastmcp_server_host: str
    fastmcp_server_port: int
    log_level: str
    db_url: str = "dummy://connection"  # Valor fictício já que não usaremos mais o banco de dados
    gemini_api_key: str
    gemini_model: str
    mcp_server_url: str
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
