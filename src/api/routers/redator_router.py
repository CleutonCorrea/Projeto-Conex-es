# src/api/routers/redator_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from fastmcp import Client
from fastmcp.client.transports import SSETransport
from src.config import load_settings

import json
import uuid
import traceback
import time

router = APIRouter()

# A URL do seu endpoint SSE do MCP
settings = load_settings()
MCP_SERVER_URL = settings.mcp_server_url

class DocumentoRequest(BaseModel):
    action: str
    dados_estruturados: Dict[str, Any]
    session_id: str
    texto_extraido: str
    prompt_usuario: Optional[str] = None
    conteudo_resultado_markdown: Optional[str] = None

class DocumentoResponse(BaseModel):
    documento_gerado: str
    modelo_usado: str
    timestamp: str
    tempo_total: float
    tempo_redator: float
    tempo_revisor: float

@router.post("/gerar-documento", response_model=DocumentoResponse)
async def gerar_documento(
    payload: DocumentoRequest
):
    """
    Recebe o texto extraído, os dados estruturados e a ação selecionada.
    Chama a tool do agente redator no servidor MCP.
    Também mede e salva o tempo de execução de cada etapa.
    """
    try:
        mcp_payload = {
            "texto_extraido": payload.texto_extraido,
            "structured_data": payload.dados_estruturados,
            "action": payload.action,
            "session_id": payload.session_id,
            "prompt_usuario": payload.prompt_usuario,
            "conteudo_resultado_markdown": payload.conteudo_resultado_markdown
        }
        # 1) chama o MCP
        transport = SSETransport(url=MCP_SERVER_URL)
        client = Client(transport)
        async with client:
            # Medir tempo do redator
            inicio_redator = time.time()
            print(f"📄 Chamando tool redactor_gerar_documento_tool")
            raw = await client.call_tool("redactor_gerar_documento_tool", mcp_payload)
            tempo_redator = time.time() - inicio_redator
            print(f"📄 Tempo do redator: {tempo_redator:.2f} segundos")

            text_obj = raw[0]

            payload_revisor = {
                "texto_final": text_obj.text,
                "conteudo_resultado_markdown": payload.conteudo_resultado_markdown
            }
            
            # Medir tempo do revisor
            inicio_revisor = time.time()
            print(f"📄 Chamando tool revisor_revisao_tool")
            raw_revisor = await client.call_tool("revisor_revisao_tool", payload_revisor)
            tempo_revisor = time.time() - inicio_revisor
            print(f"📄 Tempo do revisor: {tempo_revisor:.2f} segundos")
            
            text_obj_revisor = raw_revisor[0]
            json_str = text_obj_revisor.text
            data = json.loads(json_str)  # agora data é { "documento_gerado": "...", "modelo_usado": "...", "timestamp": "..." }
            print(f"📄 Retornando documento gerado")
            
            # Salvar os tempos de execução e informações no banco de dados
            tempo_total = tempo_redator + tempo_revisor
            print(f"📄 Tempo total: {tempo_total:.2f} segundos")
              # Log informações diretamente sem usar função externa
            print(f"[INFO] Decisão processada: {payload.action}")
            print(f"[INFO] Tempo total: {tempo_total:.2f}s")
            print(f"[INFO] Tempo redator: {tempo_redator:.2f}s, Tempo revisor: {tempo_revisor:.2f}s")
            if payload.prompt_usuario:
                print(f"[INFO] Prompt do usuário: {payload.prompt_usuario}")
            
            # Adicionar tempos no resultado
            data["tempo_total"] = tempo_total
            data["tempo_redator"] = tempo_redator
            data["tempo_revisor"] = tempo_revisor
            
            return data

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar documento: {str(e)}")
