# services/llm.py
from google import genai
from src.config import load_settings
import re
from typing import Dict, Union, Optional, Any
import json
from google.genai import types

settings = load_settings()

# Inicializa o client Gemini uma vez
_gemini_client: genai.Client = genai.Client(api_key=settings.gemini_api_key)


def get_gemini_client() -> genai.Client:
    """Retorna o client já configurado para chamadas Gemini."""
    return _gemini_client


def build_generation_config(
    model_id: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = None,
    system_instruction: Optional[str] = None,
    response_mime_type: Optional[str] = None,
    response_schema: Optional[Dict] = None,
) -> tuple[str, types.GenerateContentConfig]:
    """
    Monta o par (model_id, GenerateContentConfig) para uso nas chamadas LLM.

    Args:
        model_id: ID do modelo (padrão em settings).
        temperature: Controla aleatoriedade.
        max_output_tokens: Tamanho máximo da resposta.
        system_instruction: Instrução de sistema para o LLM.
        response_mime_type: Tipo MIME da resposta (ex: 'application/json').
        response_schema: Schema para respostas estruturadas.
    """
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_instruction=system_instruction,
        response_mime_type=response_mime_type,
    )
    if response_schema:
        config.response_schema = response_schema
    return (model_id or settings.gemini_model, config)


def parse_resposta_gemini(resposta: str) -> Union[Dict, str]:
    """
    Processa a resposta da Gemini:
    - Se contiver um bloco ```json ... ```, extrai esse conteúdo e faz json.loads.
    - Substitui literais JSON por None/True/False se necessário.
    - Se json.loads falhar, devolve a resposta original como string (Markdown).
    """
    if not resposta or not resposta.strip():
        raise ValueError("Resposta vazia")

    # 1) Tentar encontrar um bloco ```json ... ```
    bloco_json = None
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", resposta, flags=re.DOTALL|re.IGNORECASE)
    if m:
        bloco_json = m.group(1)
    else:
        # talvez a resposta já venha sem fence, mas seja JSON puro
        # tentar isolar o trecho entre a primeira '{' e última '}'
        start = resposta.find('{')
        end   = resposta.rfind('}')
        if start != -1 and end != -1 and end > start:
            bloco_json = resposta[start:end+1]

    if bloco_json:
        # limpando possíveis backticks ou espaços
        texto = bloco_json.strip("`\n ")
        # normalizar literais JSON (null, true, false)
        texto = re.sub(r'\bnull\b', 'null', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\btrue\b', 'true', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\bfalse\b', 'false', texto, flags=re.IGNORECASE)

        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            # não era um JSON válido – vamos cair no fallback
            pass

    # 2) Fallback: devolve raw (incluindo Markdown) para renderização posterior
    return resposta


def extrair_dados_estruturados(texto: str, prompt: str) -> Union[Dict, str]:
    """
    Usa o modelo Gemini para gerar uma resposta e converte para JSON estruturado.
    """
    client = get_gemini_client()
    model_id, config = build_generation_config(
        temperature=0.2
    )
    response = client.models.generate_content(
        model=model_id,
        contents=f"{prompt}\n\nTexto:\n{texto}",
        config=config
    )
    # Garante que .text não seja None antes do parsing
    return parse_resposta_gemini(response.text or "")


async def gerar_resposta_llm(prompt: str) -> str:
    """
    Envia um prompt ao modelo Gemini e retorna a resposta de texto.
    """
    client = get_gemini_client()
    model_id, config = build_generation_config(
        system_instruction=None,
        max_output_tokens=None
    )
    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=config
    )
    # Retorna o texto gerado ou fallback para string da resposta
    text = getattr(response, 'text', None)
    if text:
        return text.strip()
    return str(response)
