# Autenticação da API

A API do Projeto Conexões utiliza autenticação Bearer Token para proteger as rotas contra acessos não autorizados.

## Como funciona

Todas as rotas da API (exceto `/status`) exigem um token de autenticação que deve ser enviado no header HTTP `Authorization` em todas as requisições:

```
Authorization: Bearer seu_token_aqui
```

## Gerar token inicial

Para gerar um token inicial, execute o script:

```bash
python generate_token.py
```

Isso criará um token aleatório e seguro e o salvará no arquivo `.env`. Este token será carregado automaticamente quando o servidor for iniciado.

## Gerar novos tokens (admin)

Novos tokens podem ser gerados através da rota administrativa:

```
POST /admin/generate-token
```

Corpo da requisição (JSON):
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**IMPORTANTE**: Em ambiente de produção, altere as credenciais de administrador padrão no arquivo `token_router.py`.

## Exemplo de uso do token em requisições

### Python (requests)
```python
import requests

API_TOKEN = "seu_token_aqui"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# Exemplo de requisição com autenticação
response = requests.post(
    "http://localhost:8001/extrair-dados",
    files={"arquivo": open("documento.pdf", "rb")},
    headers=headers
)
```

### cURL
```bash
curl -X POST "http://localhost:8001/extrair-dados" \
  -H "Authorization: Bearer seu_token_aqui" \
  -F "arquivo=@documento.pdf"
```

## Segurança

O token é verificado utilizando uma comparação segura contra timing attacks. Se um token inválido ou expirado for fornecido, a API retornará um erro 401 Unauthorized.
