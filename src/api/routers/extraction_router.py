# src/api/routers/extraction_router.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastmcp import Client
from fastmcp.client.transports import SSETransport
from src.config import load_settings

import base64
import json
import traceback
import uuid
import time
from typing import Optional, Dict, Any

router = APIRouter()

# URL do servidor MCP
settings = load_settings()
MCP_SERVER_URL = settings.mcp_server_url

class ExtracaoResponse(BaseModel):
    dados_estruturados: Dict[str, Any]

@router.post("/extrair-dados", response_model=ExtracaoResponse)
async def extrair_dados(arquivo: UploadFile = File(...)):
    try:
        session_id = str(uuid.uuid4())
        conteudo = await arquivo.read()
        texto_base64 = base64.b64encode(conteudo).decode("utf-8")

        # Medir tempo de extração do PDF
        t0_pdf = time.perf_counter()
        payload_pdf = {
            "base64_pdf": texto_base64,
            "session_id": session_id
        }
        transport = SSETransport(url=MCP_SERVER_URL)
        client = Client(transport)
        async with client:
            print(f"📄 Chamando tool extractor_pdf_text_tool")
            response_pdf = await client.call_tool("extractor_pdf_text_tool", payload_pdf)
            t1_pdf = time.perf_counter()
            tempo_pdf_segundos = t1_pdf - t0_pdf

            if isinstance(response_pdf, list) and hasattr(response_pdf[0], 'text'):
                try:
                    parsed = json.loads(response_pdf[0].text)
                except json.JSONDecodeError as e:
                    raise HTTPException(status_code=500, detail=f"Erro ao converter resposta do MCP em JSON: {e}")
            else:
                raise HTTPException(status_code=500, detail="Resposta inesperada do MCP. Esperado list[TextContent].")

            texto_extraido = parsed.get("texto")
            if not texto_extraido:
                raise HTTPException(status_code=500, detail="Texto extraído está vazio.")

            # Medir tempo de comunicação com LLM
            t0_llm = time.perf_counter()
            print(f"📄 Chamando tool extractor_structured_data_tool")
            response_structured = await client.call_tool("extractor_structured_data_tool", {"texto": texto_extraido})
            t1_llm = time.perf_counter()
            tempo_llm_segundos = t1_llm - t0_llm
            raw = response_structured[0].text.strip("`\n ")
            try:
                dados_estruturados = json.loads(raw)
            except json.JSONDecodeError:
                dados_estruturados = {"texto_raw": raw}            # Log de informações para debug

        # Retorna JSON em vez de HTML
        return ExtracaoResponse(
            dados_estruturados=dados_estruturados
        )
    except Exception as e:
        print("Erro completo:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na extração: {str(e)}")

class TextoExtrair(BaseModel):
    texto: str

@router.post("/extrair-texto", response_model=ExtracaoResponse)
async def extrair_texto(payload: TextoExtrair):
    try:
        session_id = str(uuid.uuid4())
        texto_entrada = payload.texto

        t0_total = time.perf_counter()
        transport = SSETransport(url=MCP_SERVER_URL)
        client = Client(transport)
        async with client:
            # Pular a extração do PDF já que o texto foi fornecido diretamente
            print(f"📄 Processando texto diretamente")
            t0_llm = time.perf_counter()
            
            # Chamar a ferramenta para obter dados estruturados
            print(f"📄 Chamando tool extractor_structured_data_tool")
            response_structured = await client.call_tool("extractor_structured_data_tool", {"texto": texto_entrada})
            t1_llm = time.perf_counter()
            tempo_llm_segundos = t1_llm - t0_llm
            
            raw = response_structured[0].text.strip("`\n ")
            try:
                dados_estruturados = json.loads(raw)
            except json.JSONDecodeError:
                dados_estruturados = {"texto_raw": raw}

        t1_total = time.perf_counter()
        tempo_total = t1_total - t0_total        # Loga informações para debug
        # Retorna JSON
        return ExtracaoResponse(
            session_id=session_id,
            texto_extraido=texto_entrada,
            dados_estruturados=dados_estruturados,
            tempo_processamento=tempo_total
        )
    except Exception as e:
        print("Erro completo:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro no processamento do texto: {str(e)}")