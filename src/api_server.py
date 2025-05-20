# src/api_server.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import datetime

from src.api.routers.extraction_router import router as extraction_router
from src.api.routers.token_router     import router as token_router
from src.config import load_settings

app = FastAPI(title="Flagrantes")

# Configuração CORS para permitir acesso à API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos os origens em ambiente de desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carrega configurações
settings = load_settings()

# inclui routers
app.include_router(extraction_router, prefix="", tags=["Extrações"])
app.include_router(token_router,     prefix="/admin", tags=["Administração"])
app.include_router(token_router,     prefix="", tags=["Tokens"])

# Middleware para sessões - mantido para funcionalidade geral
app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)

# Configuração de documentação automática da API
app.title = "API de Análise de Textos Jurídicos"
app.description = """
API para extração e análise de textos jurídicos utilizando Inteligência Artificial.

## Autenticação

Todas as rotas requerem autenticação via token Bearer. Para acessar a API:

1. Obtenha um token de acesso através do endpoint `/admin/generate-token` (requer credenciais de administrador)
2. Inclua o token em todas as requisições no header: `Authorization: Bearer seu_token_aqui`

## Funcionalidades

* `/extrair-dados` - Extrai dados de PDFs de documentos jurídicos
* `/extrair-texto` - Processa texto diretamente fornecido (sem PDF)
* `/admin/generate-token` - Gera um novo token de API (acesso administrativo)

Esta API foi desenvolvida para permitir a integração com serviços externos e automatizar o processamento de documentos jurídicos de forma segura.
"""
app.version = "1.0.0"

# rota inicial simplificada 
@app.get("/status", tags=["Sistema"])
async def status():
    return {"status": "online", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/")
async def home():
    return {
        "message": "API de Extração e Análise de Textos Jurídicos",
        "como_usar": {
            "extrair_dados": {
                "endpoint": "/extrair-dados",
                "metodo": "POST",
                "formato": "multipart/form-data",
                "parametros": {
                    "arquivo": "Arquivo PDF (application/pdf)"
                },
                "exemplo_curl": "curl -X POST -F \"arquivo=@caminho/para/arquivo.pdf\" http://localhost:8001/extrair-dados",
                "exemplo_python": "requests.post('http://localhost:8001/extrair-dados', files={'arquivo': open('caminho/arquivo.pdf', 'rb')})",
                "resposta_esperada": {
                    "session_id": "Identificador único da sessão",
                    "texto_extraido": "Texto extraído do PDF",
                    "dados_estruturados": "Dados estruturados extraídos do texto",
                    "tempo_processamento": "Tempo de processamento em segundos"
                }
            }
        },
        "documentacao": "/docs",
        "versao": app.version
    }

if __name__ == "__main__":
    import uvicorn
    settings = load_settings()
    uvicorn.run(
        "src.api_server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
