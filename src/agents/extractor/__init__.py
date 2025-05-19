from fastmcp import FastMCP
from src.config import load_settings
from src.services.llm import extrair_dados_estruturados
from .prompts import EXTRACTION_PROMPT
import os
import base64
import tempfile
import fitz
import json
import datetime
from pathlib import Path
from .preprocess import ExtratorPDFProjetos

settings = load_settings()

# Instancia MCP local para o agente extractor
extractor_mcp = FastMCP(name="extractor")

# Tool: extrai texto de PDF
@extractor_mcp.tool()
def pdf_text_tool(base64_pdf: str, session_id: str) -> dict:
    """
    Extrai o texto estruturado de um arquivo PDF codificado em base64
    usando o extrator avançado ExtratorPDFProjetos.
    """
    try:
        # Decodificar PDF de base64
        decoded = base64.b64decode(base64_pdf)
        
        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(decoded)
            tmp_path = tmp_file.name
        
        # Criar caminhos temporários para saída
        temp_dir = Path(tempfile.gettempdir()) / "projeto_conexoes" / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        saida_md = temp_dir / "output.md"
        saida_json = temp_dir / "output.json"
        
        # Processar usando o extrator avançado
        extrator = ExtratorPDFProjetos()
        dados = extrator.extrair_completo(Path(tmp_path), saida_md, saida_json)
        
        # Ler o texto processado do arquivo markdown
        texto_extraido = saida_md.read_text(encoding="utf-8") if saida_md.exists() else ""
        
        # Limpar arquivos temporários
        os.remove(tmp_path)
        
        
        if not texto_extraido.strip():
            return {"erro": "Não foi possível extrair texto do PDF."}
        
        # Manter formato de resposta compatível com a implementação atual
        # mas adicionar dados estruturados extras
        resposta = {
            "texto": texto_extraido.strip(),
            "metadados": {
                "total_paginas": dados["total_paginas"],
                "campos_estruturados": dados["resumo"]["total_campos_estruturados"],
                "navegadores_laterais": dados["resumo"]["total_navegadores_laterais"],
                "tipos_documento": dados["resumo"]["tipos_documento"],
                "hierarquia": dados["resumo"]["hierarquia_detectada"]
            }
        }
        
        return resposta
    except Exception as e:
        return {"erro": f"Erro na extração do PDF: {str(e)}"}

# Tool: extrai dados estruturados usando Gemini
@extractor_mcp.tool()
def structured_data_tool(texto: str) -> dict:
    """
    Utiliza Gemini via utilitário centralizado para extrair dados estruturados de um texto jurídico.
    """
    try:
        return extrair_dados_estruturados(texto, EXTRACTION_PROMPT)
    except Exception as e:
        return {"erro": f"Erro ao processar resposta do Gemini: {str(e)}"}

# Prompt MCP para extração jurídica
@extractor_mcp.prompt()
def extracao_juridica_prompt() -> str:
    """
    Prompt principal para extração jurídica de autos de prisão em flagrante e comunicados de mandado.
    """
    return EXTRACTION_PROMPT

# Se quiser adicionar prompts customizados, use o decorador @extractor_mcp.prompt() aqui e importe o texto do arquivo prompts.py
