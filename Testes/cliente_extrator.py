"""
Cliente simples para testar a rota de extração de dados da API.
Este script envia um arquivo PDF para a API e exibe os resultados da extração.
"""

import requests
import os
import time
import sys
import json
from datetime import datetime

# URL base da API
API_BASE_URL = "http://localhost:8001"
EXTRACTOR_ENDPOINT = f"{API_BASE_URL}/extrair-dados"

def extrair_texto_de_pdf(caminho_pdf):
    """Enviar um PDF para a API e extrair o texto e dados estruturados"""
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho_pdf):
        print(f"Erro: Arquivo '{caminho_pdf}' não encontrado")
        return None
    
    # Obter o tamanho do arquivo
    tamanho_arquivo = os.path.getsize(caminho_pdf) / (1024 * 1024)  # Tamanho em MB
    print(f"Arquivo: {caminho_pdf}")
    print(f"Tamanho: {tamanho_arquivo:.2f} MB")
    
    # Preparar arquivo para envio
    with open(caminho_pdf, 'rb') as arquivo:
        arquivos = {'arquivo': (os.path.basename(caminho_pdf), arquivo, 'application/pdf')}
        
        # Iniciar cronômetro para medir o tempo total
        print(f"Enviando PDF para extração via API...")
        inicio = time.time()
        
        # Fazer a requisição POST
        try:
            resposta = requests.post(EXTRACTOR_ENDPOINT, files=arquivos)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com a API: {e}")
            print("Verifique se o servidor está online na porta 8001")
            return None
    
    # Calcular tempo total
    tempo_total = time.time() - inicio
    
    # Verificar se a requisição foi bem-sucedida
    if resposta.status_code == 200:
        dados = resposta.json()
        
        print("\n" + "="*70)
        print(f"EXTRAÇÃO REALIZADA COM SUCESSO!")
        print("="*70)
        print(f"ID da sessão: {dados.get('session_id', 'N/A')}")
        print(f"Tempo reportado pela API: {dados.get('tempo_processamento', 0):.2f} segundos")
        print(f"Tempo total incluindo transferência: {tempo_total:.2f} segundos")
        
        # Mostrar informações sobre os dados extraídos
        dados_estruturados = dados.get('dados_estruturados', {})
        
        print(f"Dados estruturados: {len(dados_estruturados)} campos")
        
        # Salvar resultados
        data_hora = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Salvar texto extraído
        nome_arquivo_texto = f"texto_extraido_{data_hora}.txt"
        with open(nome_arquivo_texto, "w", encoding="utf-8") as arquivo:
            arquivo.write(dados_estruturados.get('texto_raw', ''))
        print(f"\nTexto extraído salvo em: {nome_arquivo_texto}")
        
        # Salvar resposta completa em JSON
        nome_arquivo_json = f"resposta_api_{data_hora}.json"
        with open(nome_arquivo_json, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)
        print(f"Resposta completa da API salva em: {nome_arquivo_json}")
        
        return dados
    else:
        print(f"Erro na extração: {resposta.status_code} - {resposta.text}")
        return None

def verificar_servidor():
    """Verifica se o servidor da API está online"""
    try:
        resposta = requests.get(f"{API_BASE_URL}", timeout=3)
        if resposta.status_code == 200:
            return True
        print(f"API respondeu com código {resposta.status_code}.")
        return False
    except requests.exceptions.RequestException:
        return False

if __name__ == "__main__":
    # Definir o caminho para o arquivo de teste
    arquivo_padrao = r"Testes\202300255099 - Proposta de Projeto - Gestão Proativa v4.pdf"
    
    # Banner de início
    print("\n" + "="*70)
    print("   CLIENTE DE TESTE PARA API DE EXTRAÇÃO DE DADOS DE PDF")
    print("="*70 + "\n")
    
    # Verificar se o servidor está online
    print("Verificando conexão com o servidor da API...")
    if not verificar_servidor():
        print("Erro: O servidor da API não está disponível.")
        print("Verifique se o servidor está em execução na porta 8001.")
        sys.exit(1)
    
    print("Servidor da API está online!")
    
    # Determinar o arquivo a ser processado
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and sys.argv[1].lower().endswith('.pdf'):
        arquivo_pdf = sys.argv[1]
    else:
        if len(sys.argv) > 1:
            print(f"Arquivo não encontrado ou não é um PDF: {sys.argv[1]}")
        print(f"Usando arquivo de teste padrão: {arquivo_padrao}")
        arquivo_pdf = arquivo_padrao
    
    # Executar a extração
    extrair_texto_de_pdf(arquivo_pdf)
