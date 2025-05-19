from fastmcp import FastMCP, Context
from src.config import load_settings
from src.services.llm import gerar_resposta_llm  # Centraliza chamada à LLM
from .prompts import PRISAO_PREVENTIVA_PROMPT, LIBERDADE_PROVISORIA_PROMPT, RELAXAMENTO_PRISAO_PROMPT
import datetime
import json
from typing import Dict, Any

settings = load_settings()

redactor_mcp = FastMCP(name="Redator")

@redactor_mcp.resource("resource://texto_extraido")
async def texto_extraido_resource(ctx: Context) -> str:
    payload = getattr(ctx, "payload", {}) or {}
    return payload.get("texto_extraido", "")

@redactor_mcp.prompt("prisao_preventiva_prompt")
async def prisao_preventiva_prompt(ctx: Context, texto_extraido: str, structured_data: str, prompt_usuario: str, conteudo_resultado_markdown: str) -> str:
    instrucoes_especificas = f"INSTRUÇÕES ESPECÍFICAS FORNECIDAS PELO USUÁRIO:\n{prompt_usuario}\n\n" if prompt_usuario else ""
    return PRISAO_PREVENTIVA_PROMPT + "\n" + instrucoes_especificas + f"\nTEXTO EXTRAÍDO DO PDF:\n{texto_extraido}\nDADOS RESUMIDOS DO CASO:\n{conteudo_resultado_markdown}"

@redactor_mcp.prompt("liberdade_provisoria_prompt")
async def liberdade_provisoria_prompt(ctx: Context, texto_extraido: str, structured_data: str, prompt_usuario: str, conteudo_resultado_markdown: str) -> str:
    instrucoes_especificas = f"INSTRUÇÕES ESPECÍFICAS FORNECIDAS PELO USUÁRIO:\n{prompt_usuario}\n\n" if prompt_usuario else ""
    return LIBERDADE_PROVISORIA_PROMPT + "\n" + instrucoes_especificas + f"\nTEXTO EXTRAÍDO DO PDF:\n{texto_extraido}\nDADOS RESUMIDOS DO CASO:\n{conteudo_resultado_markdown}"

@redactor_mcp.prompt("relaxamento_prisao_prompt")
async def relaxamento_prisao_prompt(ctx: Context, texto_extraido: str, structured_data: str, prompt_usuario: str, conteudo_resultado_markdown: str) -> str:
    instrucoes_especificas = f"INSTRUÇÕES ESPECÍFICAS FORNECIDAS PELO USUÁRIO:\n{prompt_usuario}\n\n" if prompt_usuario else ""
    return RELAXAMENTO_PRISAO_PROMPT + "\n" + instrucoes_especificas + f"\nTEXTO EXTRAÍDO DO PDF:\n{texto_extraido}\nDADOS RESUMIDOS DO CASO:\n{conteudo_resultado_markdown}"

@redactor_mcp.tool("gerar_documento_tool")
async def gerar_documento(
    ctx: Context,
    texto_extraido: str,
    structured_data: str,
    action: str,
    prompt_usuario: str,
    conteudo_resultado_markdown: str,
    session_id: str,
) -> Dict[str, Any]:
    """
    Gera um documento jurídico a partir dos dados extraídos, tipo de ação e instruções do usuário.
    Seleciona o prompt adequado conforme a ação, envia ao módulo centralizado da LLM e retorna o texto gerado.
    """
    acao_normalizada = action.strip().lower()
    mapa_prompts = {
        "prisão preventiva": prisao_preventiva_prompt,
        "prisao preventiva": prisao_preventiva_prompt,
        "preventiva": prisao_preventiva_prompt,
        "liberdade provisória": liberdade_provisoria_prompt,
        "liberdade provisoria": liberdade_provisoria_prompt,
        "provisória": liberdade_provisoria_prompt,
        "provisoria": liberdade_provisoria_prompt,
        "liberdade": liberdade_provisoria_prompt,
        "relaxamento da prisão": relaxamento_prisao_prompt,
        "relaxamento da prisao": relaxamento_prisao_prompt,
        "relaxamento": relaxamento_prisao_prompt,
        "relaxar": relaxamento_prisao_prompt,
    }
    prompt_func = mapa_prompts.get(acao_normalizada)
    if not prompt_func:
        erro_msg = (
            f"Ação '{action}' não reconhecida. Tipos válidos: "
            "'prisão preventiva', 'liberdade provisória', 'relaxamento da prisão'."
        )
        await ctx.error(erro_msg)
        raise ValueError(erro_msg)
    await ctx.info(f"Recebido pedido para gerar documento do tipo: {acao_normalizada}")
    prompt_text = await prompt_func(ctx, texto_extraido, structured_data, prompt_usuario, conteudo_resultado_markdown)
    await ctx.info(f"Enviando prompt para o módulo centralizado da LLM para gerar documento de {acao_normalizada}")
    documento_texto = await gerar_resposta_llm(prompt_text)
    timestamp = datetime.datetime.utcnow().isoformat()
    return {
        "documento_gerado": documento_texto,
        "modelo_usado": settings.gemini_model,
        "tipo_documento": acao_normalizada,
        "timestamp": timestamp
    }
