import asyncio
from fastmcp import FastMCP
from src.config import load_settings
from src.agents import redactor_mcp
from src.agents.revisor import revisor_mcp
from src.agents.extractor import extractor_mcp
from src.agents.redactor import redactor_mcp

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
    mcp.mount("revisor", revisor_mcp)
    mcp.mount("extractor", extractor_mcp)
    mcp.mount("redactor", redactor_mcp)

if __name__ == "__main__":

    # monta agentes
    asyncio.run(setup())
    # Rodar o servidor com transporte SSE
    mcp.run(transport="sse")
