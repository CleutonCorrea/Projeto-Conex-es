"""
Cliente para teste de API remota.
Este script permite enviar um PDF para uma API remota para extração.
"""

import requests
import os
import time
import sys
import json
from datetime import datetime

def extrair_texto_de_pdf_remoto(url_api, caminho_pdf):
    """Enviar um PDF para a API remota e extrair o texto e dados estruturados"""
    endpoint = f"{url_api}/extrair-dados"
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho_pdf):
        print(f"Erro: Arquivo '{caminho_pdf}' não encontrado")
        return None
    
    # Obter informações do arquivo
    tamanho_arquivo = os.path.getsize(caminho_pdf) / (1024 * 1024)  # Tamanho em MB
    print(f"Arquivo: {caminho_pdf}")
    print(f"Tamanho: {tamanho_arquivo:.2f} MB")
    
    # Preparar arquivo para envio
    with open(caminho_pdf, 'rb') as arquivo:
        arquivos = {'arquivo': (os.path.basename(caminho_pdf), arquivo, 'application/pdf')}
        
        # Iniciar cronômetro para medir o tempo total
        print(f"Enviando PDF para API remota ({url_api})...")
        inicio = time.time()
        
        # Fazer a requisição POST
        try:
            resposta = requests.post(endpoint, files=arquivos)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com a API remota: {e}")
            return None
    
    # Calcular tempo total
    tempo_total = time.time() - inicio
    
    # Verificar se a requisição foi bem-sucedida
    if resposta.status_code == 200:
        dados = resposta.json()
        
        print("\n" + "="*70)
        print(f"EXTRAÇÃO REMOTA REALIZADA COM SUCESSO!")
        print("="*70)
        print(f"ID da sessão: {dados.get('session_id', 'N/A')}")
        print(f"Tempo reportado pela API: {dados.get('tempo_processamento', 0):.2f} segundos")
        print(f"Tempo total incluindo transferência: {tempo_total:.2f} segundos")
        
        # Mostrar informações sobre os dados extraídos
        texto_extraido = dados.get('texto_extraido', '')
        dados_estruturados = dados.get('dados_estruturados', {})
        
        print(f"\nTexto extraído: {len(texto_extraido)} caracteres")
        print(f"Dados estruturados: {len(dados_estruturados)} campos")
        
        # Mostrar uma amostra do texto extraído
        if texto_extraido:
            print("\nAmostra do texto extraído:")
            print("-" * 50)
            amostra = texto_extraido[:500] + "..." if len(texto_extraido) > 500 else texto_extraido
            print(amostra)
            print("-" * 50)
        
        # Salvar resultados
        data_hora = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Salvar texto extraído
        nome_arquivo_texto = f"texto_extraido_remoto_{data_hora}.txt"
        with open(nome_arquivo_texto, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto_extraido)
        print(f"\nTexto extraído salvo em: {nome_arquivo_texto}")
        
        # Salvar resposta completa em JSON
        nome_arquivo_json = f"resposta_remota_{data_hora}.json"
        with open(nome_arquivo_json, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)
        print(f"Resposta completa da API salva em: {nome_arquivo_json}")
        
        return dados
    else:
        print(f"Erro na extração: {resposta.status_code} - {resposta.text}")
        return None

def verificar_servidor_remoto(url_api):
    """Verifica se o servidor da API remota está online"""
    try:
        resposta = requests.get(f"{url_api}/status", timeout=5)
        if resposta.status_code == 200:
            return True
        print(f"API remota respondeu com código {resposta.status_code}.")
        return False
    except requests.exceptions.RequestException:
        return False

if __name__ == "__main__":
    # Banner de início
    print("\n" + "="*70)
    print("   CLIENTE DE TESTE PARA API REMOTA DE EXTRAÇÃO DE DADOS DE PDF")
    print("="*70 + "\n")
    
    # Verificar os argumentos de linha de comando
    if len(sys.argv) < 2:
        print("Uso: python cliente_remoto.py <URL_API> [caminho_pdf]")
        print("Exemplo: python cliente_remoto.py https://12a3-45-6-78-9.ngrok-free.app Testes/arquivo.pdf")
        sys.exit(1)
    
    # Obter URL da API remota
    url_api = sys.argv[1].rstrip('/')
    print(f"URL da API remota: {url_api}")
    
    # Verificar se o servidor está online
    print("Verificando conexão com o servidor remoto...")
    if not verificar_servidor_remoto(url_api):
        print("Tentando continuar mesmo sem confirmação de status...")
    else:
        print("Servidor remoto respondeu com sucesso!")
    
    # Determinar o arquivo a ser processado
    arquivo_padrao = r"Testes\202300255099 - Proposta de Projeto - Gestão Proativa v4.pdf"
    
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) and sys.argv[2].lower().endswith('.pdf'):
        arquivo_pdf = sys.argv[2]
    else:
        if len(sys.argv) > 2:
            print(f"Arquivo não encontrado ou não é um PDF: {sys.argv[2]}")
        print(f"Usando arquivo de teste padrão: {arquivo_padrao}")
        arquivo_pdf = arquivo_padrao
    
    # Executar a extração
    extrair_texto_de_pdf_remoto(url_api, arquivo_pdf)
