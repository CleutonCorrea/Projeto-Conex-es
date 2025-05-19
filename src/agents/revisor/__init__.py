import datetime
import json
from typing import Dict, Any
from fastmcp import FastMCP, Context
from google.generativeai import configure, GenerativeModel
from src.config import load_settings
from .prompts import REVISOR_PROMPT
from src.services.llm import gerar_resposta_llm  # Centraliza chamada à LLM

settings = load_settings()
configure(api_key=settings.gemini_api_key)
llm = GenerativeModel(settings.gemini_model)

# Troca o nome do agente para Revisor
revisor_mcp = FastMCP(name="Revisor")

@revisor_mcp.prompt("build_prompt")
async def build_prompt(ctx: Context, texto_final: str, conteudo_resultado_markdown: Dict[str, Any]) -> str:
    """
    Monta o prompt para revisão jurídica, estruturando claramente as seções para melhor compreensão da LLM.
    """
    # Seção de instruções para a LLM
    instrucoes = (
        "INSTRUÇÕES:\n"
        "Você é um assistente jurídico. Revise o texto abaixo considerando os dados estruturados do caso. "
        "Faça sugestões de melhoria, correções e garanta clareza e precisão jurídica."
    )

    # Seção do texto a ser revisado
    texto_para_revisao = (
        f"TEXTO PARA REVISÃO:\n\n{texto_final}\n"
    )

    # Seção dos dados estruturados
    dados_estruturados = (
        f"DADOS ESTRUTURADOS DO CASO (em JSON):\n\n```json\n{json.dumps(conteudo_resultado_markdown, ensure_ascii=False, indent=4)}\n```\n"
    )

    # Monta o prompt final, separando claramente as seções
    prompt_final = (
        REVISOR_PROMPT.strip() +
        "\n\n" +
        instrucoes.strip() +
        "\n\n" +
        texto_para_revisao.strip() +
        "\n\n" +
        dados_estruturados.strip()
    )
    return prompt_final

@revisor_mcp.tool("revisao_tool")
async def revisao_tool(ctx: Context, texto_final: str, conteudo_resultado_markdown: str) -> Dict[str, Any]:
    """
    Realiza a revisão do texto final utilizando a LLM centralizada.
    """
    await ctx.info("Montando prompt para revisão jurídica.")
    prompt_text = await build_prompt(ctx, texto_final, conteudo_resultado_markdown)
    await ctx.info("Enviando prompt para o módulo centralizado da LLM para revisão.")
    texto_revisado = await gerar_resposta_llm(prompt_text)
    timestamp = datetime.datetime.utcnow().isoformat()
    return {
        "documento_gerado": texto_revisado,
        "modelo_usado": settings.gemini_model,
        "timestamp": timestamp
    }
