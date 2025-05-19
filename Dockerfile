# Usar uma imagem oficial do Python como base
FROM python:3.11-slim

# Definir o diretório de trabalho no container
WORKDIR /app

# Definir variáveis de ambiente (serão configuradas ao rodar o container)
# ENV FASTMCP_SERVER_HOST=localhost
# ENV FASTMCP_SERVER_PORT=8000
# ENV LOG_LEVEL=INFO
# ENV GEMINI_API_KEY=sua_chave_api_gemini
# ENV GEMINI_MODEL=gemini-pro
# ENV MCP_SERVER_URL=http://localhost:8000/sse
# ENV API_HOST=0.0.0.0
# ENV API_PORT=8001
# ENV JWT_SECRET_KEY=chave_secreta_temporaria_deve_ser_substituida

# Copiar o arquivo de dependências e instalar as dependências
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação para o diretório de trabalho
COPY . .

# Expor a porta em que a API está rodando
EXPOSE 8001

# Comando para rodar a aplicação
CMD ["python", "-m", "src.main"]