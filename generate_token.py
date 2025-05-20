"""
Script para gerar um token inicial para a API.
Use este script uma vez para inicializar o token de API.
"""
import secrets
import os
import dotenv
from pathlib import Path

def generate_initial_token():
    # Gera um token aleatório seguro de 32 bytes (64 caracteres em hexadecimal)
    new_token = secrets.token_hex(32)
    
    # Caminho para o arquivo .env
    env_path = Path(__file__).resolve().parent / ".env"
    
    # Verifica se o arquivo .env existe
    if env_path.exists():
        # Carrega o arquivo .env existente
        dotenv.load_dotenv(env_path)
        
        # Atualiza o valor do token no ambiente
        os.environ["API_TOKEN"] = new_token
        
        # Escreve de volta para o arquivo .env
        dotenv.set_key(env_path, "API_TOKEN", new_token)
        print(f"Token gerado e salvo no arquivo .env existente: {new_token}")
    else:
        # Cria um novo arquivo .env se não existir
        with open(env_path, "a") as f:
            f.write(f"API_TOKEN={new_token}\n")
        print(f"Arquivo .env criado com o novo token: {new_token}")
    
    print("\nInclude this token in your API requests with the header:")
    print(f"Authorization: Bearer {new_token}")

if __name__ == "__main__":
    generate_initial_token()
