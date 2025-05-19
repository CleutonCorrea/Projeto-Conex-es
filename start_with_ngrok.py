"""
Script para iniciar os servidores MCP e API com Ngrok para acesso externo
"""
import subprocess
import os
from pathlib import Path
import sys
import time
from pyngrok import ngrok
import asyncio

# Cria diretório de logs se não existir
def ensure_log_dir():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir

async def main():
    log_dir = ensure_log_dir()
    mcp_log = open(log_dir / "mcp_server.log", "w", encoding="utf-8")
    api_log = open(log_dir / "api_server.log", "w", encoding="utf-8")
    
    python_executable = sys.executable
    project_root = Path(__file__).resolve().parent
    
    print("Iniciando servidores MCP e API...")
    
    # Inicia MCP Server
    mcp_proc = subprocess.Popen(
        [python_executable, "-m", "src.mcp_server"],
        stdout=mcp_log,
        stderr=subprocess.STDOUT,
        cwd=project_root
    )
    
    # Aguardar alguns segundos para o MCP server iniciar
    time.sleep(3)
    
    # Inicia API Server
    api_proc = subprocess.Popen(
        [python_executable, "-m", "src.api_server"],
        stdout=api_log,
        stderr=subprocess.STDOUT,
        cwd=project_root
    )
    
    # Aguardar alguns segundos para o API server iniciar
    time.sleep(3)
    
    print("Servidores MCP e API iniciados. Logs em ./logs/")
    
    try:
        # Configurar e iniciar Ngrok para a porta API (8001)
        print("Configurando túnel Ngrok para a API (porta 8001)...")
        
        # Iniciar o túnel Ngrok
        public_url = ngrok.connect(8001, "http")
        print(f"\n🎉 API disponível externamente em: {public_url}")
        print("\nCompartilhe este URL com quem precisar acessar seu sistema.")
        print("Para fazer um POST para a rota de extração, use:")
        print(f"{public_url}/extrair-dados")
        print("\nPressione Ctrl+C para encerrar os servidores e o túnel.")
        
        # Mostrar URLs formatadas para fácil cópia/compartilhamento
        print("\n" + "-"*70)
        print("URLs para compartilhar:")
        print(f"API URL: {public_url}")
        print(f"Rota de extração: {public_url}/extrair-dados")
        print("-"*70 + "\n")
        
        # Manter o programa em execução até ser interrompido
        while True:
            await asyncio.sleep(1)  # Usar asyncio.sleep para permitir Ctrl+C
    
    except KeyboardInterrupt:
        print("\nEncerrando servidores e túnel...")
    finally:
        # Encerrar o túnel Ngrok
        ngrok.kill()
        
        # Encerrar os servidores
        mcp_proc.terminate()
        api_proc.terminate()
        
        # Fechar os arquivos de log
        mcp_log.close()
        api_log.close()
        
        print("Servidores e túnel encerrados.")

if __name__ == "__main__":
    # Executar o código assíncrono
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
