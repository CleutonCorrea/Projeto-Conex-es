import asyncio
from fastmcp import FastMCP
from src.config import load_settings
from src.agents.extractor import extractor_mcp

settings = load_settings()

# Cria a instância do servidor
mcp = FastMCP(
    name="MVPFlagranteServer",
    instructions="Servidor para análise de autos de prisão em flagrante.",
    host=settings.fastmcp_server_host,
    port=settings.fastmcp_server_port,
    log_level=settings.log_level
)


async def setup():
    # monta agentes e tools
    mcp.mount("extractor", extractor_mcp)

if __name__ == "__main__":

    # monta agentes
    asyncio.run(setup())
    # Rodar o servidor com transporte SSE
    mcp.run(transport="sse")
