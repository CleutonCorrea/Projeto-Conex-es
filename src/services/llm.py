# services/llm.py
import google.generativeai as genai
from src.config import load_settings
import re
from typing import Dict, Union
import json

settings = load_settings()


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


def extrair_dados_estruturados(texto: str, prompt: str) -> dict:
    """
    Usa o modelo Gemini para gerar uma resposta e converte para JSON estruturado via função utilitária.
    """
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    response = model.generate_content(f"{prompt}\n\nTexto:\n{texto}")
    resposta = response.text

    return parse_resposta_gemini(resposta)


async def gerar_resposta_llm(prompt: str) -> str:
    """
    Função centralizada para enviar prompts à LLM (Gemini) e retornar a resposta como texto.
    Pode ser expandida para logging, tratamento de exceções, etc.
    """
    model = genai.GenerativeModel(settings.gemini_model)
    response = model.generate_content(prompt)
    # Tenta acessar .text, senão pega o primeiro candidato
    if hasattr(response, "text"):
        return response.text.strip()
    elif hasattr(response, "candidates") and response.candidates:
        return response.candidates[0].content.strip()
    else:
        return str(response)
