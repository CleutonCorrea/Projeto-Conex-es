import subprocess
import os
from pathlib import Path
import sys

# Cria diretório de logs se não existir
def ensure_log_dir():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir

def main():
    log_dir = ensure_log_dir()
    mcp_log = open(log_dir / "mcp_server.log", "w", encoding="utf-8")
    api_log = open(log_dir / "api_server.log", "w", encoding="utf-8")

    python_executable = sys.executable
    project_root = Path(__file__).resolve().parent.parent
    # Inicia MCP Server
    mcp_proc = subprocess.Popen(
        [python_executable, "-m", "src.mcp_server"],
        stdout=mcp_log,
        stderr=subprocess.STDOUT,
        cwd=project_root
    )
    # Inicia API Server
    api_proc = subprocess.Popen(
        [python_executable, "-m", "src.api_server"],
        stdout=api_log,
        stderr=subprocess.STDOUT,
        cwd=project_root
    )
    print("Servidores MCP e API iniciados. Logs em ./logs/")
    try:
        mcp_proc.wait()
        api_proc.wait()
    except KeyboardInterrupt:
        print("Encerrando servidores...")
        mcp_proc.terminate()
        api_proc.terminate()
    finally:
        mcp_log.close()
        api_log.close()

if __name__ == "__main__":
    main()
