import re
import json
from typing import Union, Dict, Any

def limpar_json(raw: str) -> str:
    """
    Extrai um objeto JSON válido de uma string que pode conter texto adicional,
    marcações markdown, HTML ou outros elementos que impedem o parsing direto.
    
    Args:
        raw: A string contendo o JSON a ser extraído
        
    Returns:
        Uma string contendo apenas o objeto JSON válido
    """
    if not raw:
        return "{}"
    
    # Passo 1: Remover formatação markdown e código
    # Remove blocos de código markdown (```json ... ```)
    clean_text = re.sub(r"```(?:json)?[\s\n\r]*|```$", "", raw, flags=re.IGNORECASE)
    
    # Passo 2: Remover tags HTML comuns
    clean_text = re.sub(r"<[^>]*>", "", clean_text)
    
    # Passo 3: Tentativa de extrair um objeto JSON completo
    # Busca o primeiro bloco JSON válido (começando com { e terminando com })
    json_match = re.search(r"(\{(?:[^{}]|(?:\{[^{}]*\}))*\})", clean_text, re.DOTALL)
    if json_match:
        potential_json = json_match.group(1)
        try:
            # Verifica se é um JSON válido
            json.loads(potential_json)
            return potential_json
        except json.JSONDecodeError:
            pass  # Continua com outras abordagens se falhar
    
    # Passo 4: Tentativa de encontrar o início e fim do JSON
    # Muitas vezes o JSON começa com { e termina com } mas pode ter texto no meio
    start_idx = clean_text.find('{')
    if start_idx != -1:
        # Encontrar o último } no texto
        end_idx = clean_text.rfind('}')
        if end_idx > start_idx:
            potential_json = clean_text[start_idx:end_idx+1]
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                # Tenta encontrar uma correspondência balanceada de chaves
                open_count = 0
                for i, char in enumerate(clean_text[start_idx:], start=start_idx):
                    if char == '{':
                        open_count += 1
                    elif char == '}':
                        open_count -= 1
                        if open_count == 0:
                            potential_json = clean_text[start_idx:i+1]
                            try:
                                json.loads(potential_json)
                                return potential_json
                            except json.JSONDecodeError:
                                pass
    
    # Passo 5: Tenta extrair pares de chave-valor
    # Busca padrões como "chave": "valor" ou "chave": valor
    pairs = re.findall(r'"([^"]+)"\s*:\s*(?:"([^"]*)"|([^,}\s][^,}]*)?)', clean_text)
    if pairs:
        json_dict = {}
        for key, str_val, non_str_val in pairs:
            if str_val:
                json_dict[key] = str_val
            elif non_str_val:
                # Tenta converter para número ou booleano se apropriado
                val = non_str_val.strip()
                if val.lower() == 'true':
                    json_dict[key] = True
                elif val.lower() == 'false':
                    json_dict[key] = False
                elif val.lower() == 'null':
                    json_dict[key] = None
                else:
                    try:
                        if '.' in val:
                            json_dict[key] = float(val)
                        else:
                            json_dict[key] = int(val)
                    except ValueError:
                        json_dict[key] = val
        
        if json_dict:
            return json.dumps(json_dict)
    
    # Retorna o texto limpo como último recurso
    return clean_text.strip("`\n\r ")

def parse_json_safely(text: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Tenta extrair e analisar um JSON de uma string, retornando um dicionário seja bem-sucedido ou não.
    
    Args:
        text: A string contendo o JSON a ser analisado
        
    Returns:
        Um dicionário com o JSON parseado ou um dicionário com o texto original em caso de falha
    """
    clean_json = limpar_json(text)
    try:
        return json.loads(clean_json)
    except json.JSONDecodeError:
        # Tentativa final: remover caracteres problemáticos e tentar novamente
        try:
            # Remove caracteres invisíveis e potencialmente problemáticos
            sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', clean_json)
            # Garante que aspas duplas são usadas para strings (não aspas simples)
            sanitized = re.sub(r"'([^']*)'", r'"\1"', sanitized)
            return json.loads(sanitized)
        except json.JSONDecodeError:
            return {"texto_raw": text, "json_parcial": clean_json}