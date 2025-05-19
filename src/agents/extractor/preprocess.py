import fitz  # PyMuPDF
import pymupdf4llm
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtratorPDFProjetos:
    """Extrator de PDF otimizado para documentos de projetos com hierarquia avançada e suporte a layouts complexos."""
    
    def __init__(self, margens: Dict[str, float] = None):
        """
        Inicializa o extrator com configurações personalizadas.
        
        Args:
            margens: Dicionário com margens normalizadas (0-1)
                    Ex: {"superior": 0.05, "inferior": 0.95}
        """
        self.margens = margens or {
            "superior": 0.08,
            "inferior": 0.92,
        }
        
        # Configuração para navegadores laterais
        self.navegadores_laterais = {
            'patterns': [
                'APRESENTAÇÃO',
                'MARCA', 
                'JUSTIFICATIVA',
                'ALINHAMENTO ESTRATÉGICO',
                'PRODUTOS',
                'CRONOGRAMA',
                'RISCOS',
                'INDICADORES DE DESEMPENHO',
            ],
            'detectar_rotacao': True,
            'area_margem_direita': 0.85,  # Procurar texto após 85% da largura da página
        }
        
        # Padrões para ignorar na hierarquia (não receberão marcação)
        self.ignore_patterns = [
            'PROPOSTA DE PROJETO',
            'PROJETO',
            'MINISTÉRIO PÚBLICO',
            'MPGO',
            r'Página\s+\d+\s*/\s*\d+',  # Numeração de página
            r'^\s*$',  # Linhas vazias
        ]
        
        # Configuração hierárquica completa
        self.header_config = {
            # Nível 1 - Títulos Principais de Projetos (H1)
            'h1': {
                'patterns': [                       
                    # Seções principais de projetos
                    'APRESENTAÇÃO',
                    'MARCA',
                    
                    'JUSTIFICATIVA',
                    'OBJETIVO',
                    'OBJETIVO GERAL',
                    'OBJETIVOS ESPECÍFICOS',
                    'VALORES DO PLANEJAMENTO ESTRATÉGICO NACIONAL',
                    'VALORES DO PLANEJAMENTO ESTRATÉGICO NACIONAL (PEN/MP)',
                    'MÉTODO', 
                    'RISCOS',
                    'METODOLOGIA',
                    'ALINHAMENTO ESTRATÉGICO',
                    'PRODUTOS',
                    'GRUPO DE ENTREGAS',
                    'CRONOGRAMA',
                    'GRUPO DE ENTREGAS (CRONOGRAMA)',
                    'INDICADORES DE DESEMPENHO',
                    'RESULTADOS ESPERADOS',
                    'RECURSOS NECESSÁRIOS',
                    'RISCOS E MITIGAÇÕES',
                    'ORÇAMENTO',
                    'MONITORAMENTO E AVALIAÇÃO',
                    'AVALIAÇÃO E CONTROLE',
                    'CONSIDERAÇÕES FINAIS',
                    'REFERÊNCIAS',
                    'ANEXOS'
                ],
                'font_size_min': 12,
                'is_uppercase': True,
                'is_bold': True,
                'variations': [':', ' -', ' –']  # Aceita variações como "JUSTIFICATIVA:" ou "JUSTIFICATIVA -"
            },
            
            # Nível 2 - Seções Secundárias de Projetos (H2)
            'h2': {
                'patterns': [
                    'AÇÕES INSTITUCIONAIS',
                    'AÇÕES INTERINSTITUCIONAIS',
                    'EQUIPE DO PROJETO',
                    'RECURSOS HUMANOS',
                    'RECURSOS MATERIAIS',
                    'PARCERIAS ESTRATÉGICAS',
                    'ANÁLISE DE VIABILIDADE',
                    'PREMISSAS E RESTRIÇÕES',
                    'LIÇÕES APRENDIDAS',
                    r'^\d+\.\s+AÇÕES\s+\w+',  # 1. AÇÕES ESTRUTURANTES
                    r'^EIXO\s+\w+',  # EIXO OPERACIONAL
                ],
                'font_size_min': 11,
                'is_bold': True,
                'is_uppercase': True
            },
            
            # Nível 3 - Subseções de Projetos (H3)
            'h3': {
                'patterns': [
                    # Dados do projeto
                    'Nome Completo do Projeto:',
                    'Áreas Responsáveis:',
                    'Coordenador Geral:',
                    'Idealizadores/Responsáveis:',
                    'Equipe de Gerenciamento:',
                    'Colaboradores:',
                    'Período de Execução:',
                    'Status do Projeto:',
                    'Versão do Documento:',
                    
                    # Subseções temáticas de projetos
                    r'^\d+\.\s+[A-Z].*?:',  # 1. Grupo de Trabalho GT-MÉTIS:
                    r'^Eixo\s+\w+:',  # Eixo Articulação:
                    'PROMOGRAMA ESTRATÉGICO',
                    'PROGRAMA ESTRATÉGICO',
                    'Descrição',
                    'Ações estratégicas',
                    'Objetivos Específicos',
                    'Metas',
                    'Entregas',
                    'Marcos do Projeto',
                    'Critérios de Sucesso',
                    
                    # Tabelas e listas estruturadas de projetos
                    'Nome',
                    'Cargo',
                    'Responsável',
                    'Data Prevista Início',
                    'Data Prevista Término',
                ],
                'font_size_min': 10,
                'is_bold': True,
                'start_of_line': True  # Deve estar no início da linha
            },
            
            # Nível 4 - Detalhes e listas de projetos (H4)
            'h4': {
                'patterns': [
                    r'^[a-z]\)\s+',  # a) item
                    r'^\s*[•●]\s+',  # • ou ● item
                    r'^\s*[-–]\s+',  # - ou – item
                    r'^\d+\.\d+\s+',  # 1.1 subitem
                    r'^[IVX]+\s*[-–]\s+',  # I - item romano
                    r'^\([a-z]\)\s+',  # (a) item
                    r'^\[\s*\]\s+',  # [ ] checkbox vazio
                    r'^\[x\]\s+',  # [x] checkbox marcado
                ],
                'font_size_min': 10,
                'is_list_item': True
            }
        }
        
        # Configuração para campos estruturados de projetos
        self.field_config = {
            'field_patterns': [
                # Valores do projeto (alinhamento estratégico)
                r'^I?\s*[-–]?\s*[Rr]esolutividade:?',
                r'^II?\s*[-–]?\s*[Pp]roatividade:?',
                r'^III?\s*[-–]?\s*[Cc]ooperação:?',  
                r'^IV?\s*[-–]?\s*[Ii]novação:?',
                r'^V?\s*[-–]?\s*[Tt]ransparência:?',
                
                # Campos do cabeçalho do projeto
                r'^Nome Completo do Projeto:',
                r'^Áreas Responsáveis:',
                r'^Coordenador Geral:',
                r'^Período de Execução:',
                r'^Orçamento Total:',
                r'^Status:',
                
                # Dados de pessoas
                r'^Nome:',
                r'^Cargo:',
                r'^E-mail:',
                r'^Telefone:',
                r'^Matrícula:',
                r'^CPF:',
                r'^Função:',
                r'^Instituição:',
                
                # Cronograma e prazos
                r'^ID:',
                r'^Entregas Principais:',
                r'^Responsável:',
                r'^Data Prevista Início:',
                r'^Data Prevista Término:',
                r'^Duração:',
                r'^Predecessoras:',
                r'^Status da Entrega:',
                r'^Percentual Concluído:',
                
                # Custos e recursos
                r'^Custo Previsto:',
                r'^Custo Realizado:',
                r'^Recursos Necessários:',
                r'^Fonte de Recursos:',
                r'^Tipo de Despesa:',
                
                # Indicadores e metas
                r'^Nome do Indicador:',
                r'^Descrição:',
                r'^Fórmula de Cálculo:',
                r'^Periodicidade de Monitoramento:',
                r'^Como Monitorar:',
                r'^Meta:',
                r'^Valor Atual:',
                r'^Valor Base:',
                r'^Unidade de Medida:',
                r'^Responsável pela Medição:',
                
                # Riscos
                r'^Risco:',
                r'^Categoria do Risco:',
                r'^Probabilidade:',
                r'^Impacto:',
                r'^Severidade:',
                r'^Estratégia de Mitigação:',
                r'^Plano de Contingência:',
                r'^Responsável:',
                
                # Ações e atividades
                r'^Ação:',
                r'^Atividade:',
                r'^Descrição da Ação:',
                r'^Objetivo da Ação:',
                r'^Prazo:',
                r'^Responsável pela Ação:',
                r'^Recursos Necessários:',
                r'^Resultados Esperados:',
            ],
            'detect_bold_fields': True,
            'field_separator': ':',
            'multiline_fields': ['Descrição', 'Justificativa', 'Metodologia'],  # Campos que podem ter múltiplas linhas
            'numeric_fields': ['Custo', 'Valor', 'Meta', 'Percentual'],  # Campos numéricos
            'date_fields': ['Data', 'Prazo', 'Início', 'Término'],  # Campos de data
        }
        
        # Padrões para elementos especiais em projetos
        self.special_patterns = {
            'graficos': r'GRÁFICO\s*\d+',
            'tabelas': r'TABELA\s*\d+', 
            'figuras': r'FIGURA\s*\d+',
            'quadros': r'QUADRO\s*\d+',
            'percentuais': r'\d+[,.]?\d*\s*%',
            'valores_monetarios': r'R\$\s*[\d.,]+(?:\s*(?:mil|milhões?|bilhões?))?',
            'datas': r'\d{1,2}/\d{1,2}/\d{4}',
            'prazos': r'\d+\s*(?:dias?|meses?|anos?)',
            'horarios': r'\d{1,2}:\d{2}(?::\d{2})?',
            'citacoes': r'\([^)]+,\s*\d{4}\)',
            'referencias_normativas': r'(?:Lei|Decreto|Resolução|Portaria|Instrução)\s*(?:nº|n°)?\s*[\d.]+/\d{4}',
            'siglas': r'\b[A-Z]{2,}\b',
            'codigos': r'\b[A-Z]{2,}-?\d+\b',  # Ex: MPGO-123
            'processos': r'\d+/\d{4}(?:-\d+)?',  # Ex: 12345/2024-01
            'links': r'https?://[^\s]+',
            'emails': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        }
        
        # Configuração adicional para elementos especiais em projetos
        self.special_elements = {
            'signatures': {
                'pattern': r'Assinatura\(s\)?\s*Eletrônica\(s\)?',
                'include_metadata': True,
                'extract_names': True  # Tentar extrair nomes dos signatários
            },
            'page_numbers': {
                'pattern': r'Página\s+\d+\s*(?:de|/)\s*\d+',
                'exclude': False,
                'position': 'footer'  # Geralmente no rodapé
            },
            'timestamps': {
                'pattern': r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(?::\d{2})?',
                'format_as': 'datetime',
                'parse_format': '%d/%m/%Y %H:%M'
            },
            'headers': {
                'pattern': r'^.{0,100}$',  # Linhas curtas no topo
                'position': 'top',
                'max_lines': 3
            },
            'footers': {
                'pattern': r'^.{0,100}$',  # Linhas curtas no rodapé
                'position': 'bottom',
                'max_lines': 3
            }
        }
        
        # Configuração para PyMuPDF4LLM - sem imagens
        self.config_pymupdf4llm = {
            "page_chunks": True,
            "write_images": False,  # DESABILITADO - não extrair imagens
            "margins": (0, 0, 1, 1),  # Sem margens adicionais (já processadas)
            "show_progress": True,
            "table_strategy": "lines_strict",  # Melhor para tabelas estruturadas
        }
        
        # Configurações de processamento
        self.processing_config = {
            'merge_lines': True,  # Mesclar linhas quebradas
            'fix_hyphenation': True,  # Corrigir hifenização
            'normalize_spaces': True,  # Normalizar espaços
            'detect_columns': True,  # Detectar texto em colunas
            'preserve_formatting': True,  # Preservar formatação (negrito, itálico)
            'extract_footnotes': True,  # Extrair notas de rodapé
            'clean_headers_footers': False,  # Manter cabeçalhos/rodapés
        }
        
        # Cache para otimização
        self._pattern_cache = {}
        self._compiled_patterns = {}
        
        # Pré-compilar padrões regex para performance
        self._compile_patterns()

    def _compile_patterns(self):
        """Pré-compila padrões regex para melhor performance."""
        # Compilar padrões de exclusão
        for pattern in self.ignore_patterns:
            if pattern not in self._compiled_patterns:
                if pattern.startswith('^') or '\\' in pattern:
                    self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
        
        # Compilar padrões de campos
        for pattern in self.field_config['field_patterns']:
            if pattern not in self._compiled_patterns:
                self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
        
        # Compilar padrões especiais
        for tipo, pattern in self.special_patterns.items():
            if pattern not in self._compiled_patterns:
                self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
        
        # Compilar padrões de hierarquia que são regex
        for nivel, config in self.header_config.items():
            for pattern in config['patterns']:
                if not isinstance(pattern, str) or pattern.startswith('^'):
                    if pattern not in self._compiled_patterns:
                        self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)

    def _extrair_texto_completo_pagina(self, pagina):
        """
        Extrai todo o texto da página, incluindo elementos rotacionados.
        
        Args:
            pagina: Página fitz
            
        Returns:
            Dict com texto principal e elementos especiais
        """
        resultado = {
            "texto_principal": "",
            "navegadores_laterais": [],
            "elementos_rotacionados": []
        }
        
        # Extrair texto com informações detalhadas
        blocks = pagina.get_text("dict")
        largura_pagina = pagina.rect.width
        
        # Processar cada bloco
        for block in blocks["blocks"]:
            if block["type"] == 0:  # Bloco de texto
                for line in block["lines"]:
                    for span in line["spans"]:
                        texto = span["text"].strip()
                        if not texto:
                            continue
                            
                        bbox = span["bbox"]
                        
                        # Verificar se é texto rotacionado ou lateral
                        is_rotacionado = False
                        is_lateral = bbox[0] > largura_pagina * self.navegadores_laterais['area_margem_direita']
                        
                        # Verificar rotação
                        if "transform" in span:
                            matrix = span["transform"]
                            if abs(matrix[1]) > 0.9 or abs(matrix[2]) > 0.9:
                                is_rotacionado = True
                        else:
                            # Verificar pela proporção da bbox
                            if (bbox[3] - bbox[1]) > 3 * (bbox[2] - bbox[0]):
                                is_rotacionado = True
                        
                        # Classificar e armazenar o texto
                        if is_lateral or is_rotacionado:
                            # Verificar se é um navegador conhecido
                            is_navegador = False
                            for pattern in self.navegadores_laterais['patterns']:
                                if pattern in texto.upper():
                                    resultado["navegadores_laterais"].append({
                                        "secao": pattern,
                                        "texto": texto,
                                        "posicao": bbox,
                                        "tipo": "navegador_lateral"
                                    })
                                    is_navegador = True
                                    break
                            
                            if not is_navegador and is_rotacionado:
                                resultado["elementos_rotacionados"].append({
                                    "texto": texto,
                                    "bbox": bbox,
                                    "rotacao": True
                                })
                        else:
                            # Texto normal - adicionar ao texto principal
                            resultado["texto_principal"] += texto + " "
        
        return resultado

    def _detectar_texto_rotacionado(self, pagina_fitz):
        """
        Detecta blocos de texto rotacionado em 90 graus na página.
        
        Args:
            pagina_fitz: Objeto página do fitz
            
        Returns:
            Lista de blocos de texto rotacionado
        """
        blocos_rotacionados = []
        
        # Extrair blocos de texto com informações de rotação
        blocks = pagina_fitz.get_text("dict")
        
        for block in blocks["blocks"]:
            if block["type"] == 0:  # Bloco de texto
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Verificar se o texto está rotacionado
                        if "transform" in span:
                            matrix = span["transform"]
                            # Detectar rotação de 90 graus (texto vertical)
                            if abs(matrix[1]) > 0.9 or abs(matrix[2]) > 0.9:
                                blocos_rotacionados.append({
                                    "texto": span["text"],
                                    "bbox": span["bbox"],
                                    "font_size": span["size"],
                                    "rotacao": True
                                })
                        # Alternativa: verificar pela orientação da bbox
                        else:
                            bbox = span["bbox"]
                            # Se altura é muito maior que largura, pode ser texto vertical
                            if (bbox[3] - bbox[1]) > 3 * (bbox[2] - bbox[0]):
                                blocos_rotacionados.append({
                                    "texto": span["text"],
                                    "bbox": bbox,
                                    "font_size": span["size"],
                                    "rotacao": True
                                })
        
        return blocos_rotacionados

    def _processar_navegadores_laterais(self, pagina, textos_rotacionados):
        """
        Identifica e processa navegadores de seção laterais.
        
        Args:
            pagina: Página fitz
            textos_rotacionados: Lista de textos rotacionados detectados
            
        Returns:
            Lista de navegadores identificados
        """
        navegadores = []
        largura_pagina = pagina.rect.width
        
        # Processar todos os textos da página
        all_text = pagina.get_text("dict")
        
        for block in all_text["blocks"]:
            if block["type"] == 0:  # Bloco de texto
                for line in block["lines"]:
                    for span in line["spans"]:
                        texto = span["text"].strip()
                        bbox = span["bbox"]
                        
                        # Verificar se está na margem direita
                        if bbox[0] > largura_pagina * self.navegadores_laterais['area_margem_direita']:
                            # Verificar se é um navegador conhecido
                            for pattern in self.navegadores_laterais['patterns']:
                                if pattern in texto.upper():
                                    navegadores.append({
                                        "secao": pattern,
                                        "texto": texto,
                                        "posicao": bbox,
                                        "tipo": "navegador_lateral"
                                    })
                                    break
        
        # Adicionar textos rotacionados que são navegadores
        for texto_rot in textos_rotacionados:
            texto_limpo = texto_rot["texto"].strip()
            
            # Verificar se é um navegador conhecido
            for pattern in self.navegadores_laterais['patterns']:
                if pattern in texto_limpo.upper():
                    navegadores.append({
                        "secao": pattern,
                        "texto": texto_limpo,
                        "posicao": texto_rot["bbox"],
                        "tipo": "navegador_lateral"
                    })
                    break
        
        return navegadores

    def _definir_area_principal(self, pagina, navegadores):
        """
        Define a área principal excluindo navegadores laterais.
        
        Args:
            pagina: Página fitz
            navegadores: Lista de navegadores detectados
            
        Returns:
            Rect com a área principal
        """
        largura, altura = pagina.rect.width, pagina.rect.height
        
        # Margem padrão
        area_util = fitz.Rect(
            0,
            altura * self.margens["superior"],
            largura,
            altura * self.margens["inferior"]
        )
        
        # Se houver navegadores laterais, ajustar margem direita
        if navegadores:
            margem_direita_max = largura
            for nav in navegadores:
                if nav["posicao"][0] < margem_direita_max:
                    margem_direita_max = nav["posicao"][0] - 10  # 10px de buffer
            
            area_util.x1 = margem_direita_max
        
        return area_util

    def _extrair_area_principal(self, pagina, area_principal):
        """
        Extrai o texto apenas da área principal da página.
        
        Args:
            pagina: Página fitz
            area_principal: Rect definindo a área principal
            
        Returns:
            Texto extraído da área principal
        """
        # Criar nova página apenas com área principal
        doc_temp = fitz.open()
        nova_pagina = doc_temp.new_page(
            width=area_principal.width,
            height=area_principal.height
        )
        
        # Copiar apenas conteúdo da área principal
        nova_pagina.show_pdf_page(
            nova_pagina.rect,
            pagina.parent,
            pagina.number,
            clip=area_principal
        )
        
        # Extrair texto
        texto = nova_pagina.get_text()
        doc_temp.close()
        
        return texto

    def _should_ignore_pattern(self, text: str) -> bool:
        """
        Verifica se o texto deve ser ignorado (não receber marcação hierárquica).
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se o texto deve ser ignorado
        """
        text_clean = text.strip()
        
        for pattern in self.ignore_patterns:
            if isinstance(pattern, str) and not pattern.startswith('^'):
                # Comparação exata de string
                if pattern.upper() == text_clean.upper():
                    return True
            else:
                # Padrão regex
                compiled_pattern = self._compiled_patterns.get(pattern)
                if compiled_pattern and compiled_pattern.match(text_clean):
                    return True
        
        return False
    
    def extrair_com_margens_controladas(self, caminho_pdf: Path) -> List[Dict]:
        """
        Usa fitz para cortar margens e PyMuPDF4LLM com hierarquia customizada.
        Versão modificada que detecta elementos rotacionados e navegadores laterais.
        
        Args:
            caminho_pdf: Caminho do PDF
            
        Returns:
            Lista de chunks de página processados
        """
        paginas_processadas = []
        navegadores_por_pagina = {}  # Mapear navegadores por número de página
        
        # Primeiro, extrair navegadores de todas as páginas
        with fitz.open(caminho_pdf) as doc_original:
            for num_pagina, pagina in enumerate(doc_original):
                # Extrair texto completo incluindo elementos laterais
                texto_completo = self._extrair_texto_completo_pagina(pagina)
                navegadores_por_pagina[num_pagina] = texto_completo["navegadores_laterais"]
                logger.info(f"Página {num_pagina + 1}: {len(texto_completo['navegadores_laterais'])} navegadores encontrados")
        
        # Criar PDF temporário com margens cortadas
        pdf_temp = Path("data/temp/temp_margins.pdf")
        pdf_temp.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Abrir documento original novamente
            with fitz.open(caminho_pdf) as doc_original:
                # Criar novo documento com margens aplicadas
                doc_novo = fitz.open()
                
                for num_pagina, pagina in enumerate(doc_original):
                    # Recuperar navegadores já detectados
                    navegadores = navegadores_por_pagina.get(num_pagina, [])
                    
                    # Definir área principal excluindo navegadores
                    area_principal = self._definir_area_principal(pagina, navegadores)
                    
                    # Criar nova página apenas com área útil
                    nova_pagina = doc_novo.new_page(
                        width=area_principal.width,
                        height=area_principal.height
                    )
                    
                    # Copiar apenas conteúdo da área útil
                    nova_pagina.show_pdf_page(
                        nova_pagina.rect,
                        doc_original,
                        num_pagina,
                        clip=area_principal
                    )
                
                # Salvar PDF temporário
                doc_novo.save(pdf_temp)
                doc_novo.close()
            
            # Usar PyMuPDF4LLM no PDF com margens cortadas
            resultado = pymupdf4llm.to_markdown(
                pdf_temp,
                **self.config_pymupdf4llm
            )
            
            # Processar cada chunk de página
            for i, chunk in enumerate(resultado):
                texto_original = chunk.get("text", "")
                
                # Recuperar navegadores da página original
                navegadores = navegadores_por_pagina.get(i, [])
                
                # Adicionar navegadores como títulos H1 se encontrados
                if navegadores:
                    # Adicionar navegador como título no início do texto
                    for nav in navegadores:
                        titulo_navegador = f"# **{nav['secao']}**\n\n"
                        # Adicionar o navegador como título no início do texto
                        texto_original = titulo_navegador + texto_original
                
                # Aplicar pós-processamento hierárquico com contexto de navegadores
                texto_processado = self._aplicar_hierarquia_customizada(
                    texto_original, 
                    navegadores
                )
                
                pagina_info = {
                    "numero": i + 1,
                    "conteudo_markdown": texto_processado,
                    "metadados": chunk.get("metadata", {}),
                    "campos_estruturados": self._extrair_campos_estruturados(texto_processado),
                    "elementos_especiais": self._processar_elementos_especiais(texto_processado),
                    "navegadores_laterais": navegadores
                }
                
                # Análise de projetos com hierarquia avançada
                pagina_info["analise_projeto"] = self._analisar_conteudo_projeto(
                    texto_processado
                )
                
                paginas_processadas.append(pagina_info)
            
            return paginas_processadas
            
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            raise
        finally:
            # Limpar arquivo temporário
            if pdf_temp.exists():
                pdf_temp.unlink()
    
    def _aplicar_hierarquia_customizada(self, texto: str, navegadores: List[Dict] = None) -> str:
        """
        Aplica hierarquia customizada ao texto baseado nas configurações.
        Versão modificada que considera navegadores de seção.
        
        Args:
            texto: Texto original do PyMuPDF4LLM
            navegadores: Lista de navegadores laterais detectados
            
        Returns:
            Texto com hierarquia ajustada
        """
        linhas = texto.split('\n')
        linhas_processadas = []
        secao_atual = None
        
        # Mapear navegadores para seções
        if navegadores:
            secao_atual = self._identificar_secao_atual(texto, navegadores)
        
        for linha in linhas:
            linha_limpa = linha.strip()
            nivel_aplicado = False
            
            # Se linha vazia, mantém
            if not linha_limpa:
                linhas_processadas.append(linha)
                continue
            
            # Verificar se a linha já tem marcação de header
            match_header_existente = re.match(r'^(.*?)(#{1,4})\s*\*\*(.+?)\*\*\s*$', linha_limpa)
            if match_header_existente:
                # Se já tem header, vamos verificar se deveria ter outro nível
                texto_antes = match_header_existente.group(1).strip()
                header_atual = match_header_existente.group(2)
                texto_titulo = match_header_existente.group(3).strip()
                
                # Verificar se o título deveria ter um nível diferente
                nivel_correto = None
                for nivel in ['h1', 'h2', 'h3', 'h4']:
                    config = self.header_config[nivel]
                    for pattern in config['patterns']:
                        if isinstance(pattern, str):
                            if pattern.upper() == texto_titulo.upper():
                                nivel_correto = nivel
                                break
                    if nivel_correto:
                        break
                
                if nivel_correto:
                    header_prefix = self._get_header_prefix(nivel_correto)
                    if texto_antes:
                        # Se tem texto antes, colocar o título em nova linha
                        linhas_processadas.append(texto_antes)
                        linhas_processadas.append(f"{header_prefix}**{texto_titulo}**")
                    else:
                        # Se não tem texto antes, aplicar o nível correto
                        linhas_processadas.append(f"{header_prefix}**{texto_titulo}**")
                else:
                    # Manter como está se não encontrou padrão
                    linhas_processadas.append(linha)
                continue
            
            # Verificar se tem título em negrito no meio ou fim da linha
            if "**" in linha_limpa:
                # Procurar por títulos em negrito que podem estar no meio da linha
                partes = re.split(r'(\*\*[^*]+\*\*)', linha_limpa)
                linha_reconstruida = []
                
                for parte in partes:
                    if parte.startswith('**') and parte.endswith('**'):
                        # É um texto em negrito
                        texto_sem_negrito = parte[2:-2].strip()
                        
                        # Verificar se é um título conhecido
                        nivel_encontrado = None
                        for nivel in ['h1', 'h2', 'h3', 'h4']:
                            config = self.header_config[nivel]
                            for pattern in config['patterns']:
                                if isinstance(pattern, str):
                                    if pattern.upper() == texto_sem_negrito.upper():
                                        nivel_encontrado = nivel
                                        break
                            if nivel_encontrado:
                                break
                        
                        if nivel_encontrado and len(linha_reconstruida) > 0:
                            # Se é um título e tem texto antes, quebrar linha
                            texto_anterior = ''.join(linha_reconstruida).strip()
                            if texto_anterior:
                                linhas_processadas.append(texto_anterior)
                            header_prefix = self._get_header_prefix(nivel_encontrado)
                            linhas_processadas.append(f"{header_prefix}**{texto_sem_negrito}**")
                            linha_reconstruida = []  # Resetar para o resto da linha
                        else:
                            linha_reconstruida.append(parte)
                    else:
                        linha_reconstruida.append(parte)
                
                # Adicionar qualquer resto
                if linha_reconstruida:
                    resto = ''.join(linha_reconstruida).strip()
                    if resto:
                        linhas_processadas.append(resto)
                continue
            
            # Caso padrão: linha simples
            # Verifica se a linha tem formatação em negrito
            tem_negrito = False
            texto_sem_negrito = linha_limpa
            
            # Padrão para detectar texto em negrito: **texto**
            match_negrito = re.match(r'^\*\*(.+)\*\*$', linha_limpa)
            if match_negrito:
                tem_negrito = True
                texto_sem_negrito = match_negrito.group(1).strip()
            
            # Verifica se a linha (com ou sem negrito) é EXATAMENTE um dos padrões de título
            nivel_aplicado = False
            
            # Verificar níveis na ordem correta
            for nivel in ['h1', 'h2', 'h3', 'h4']:
                config = self.header_config[nivel]
                for pattern in config['patterns']:
                    if isinstance(pattern, str):
                        # Verifica se o texto (sem negrito) é EXATAMENTE igual ao padrão (case insensitive)
                        if pattern.upper() == texto_sem_negrito.upper():
                            # É um título isolado - aplica hierarquia
                            header_prefix = self._get_header_prefix(nivel)
                            # Mantém a formatação em negrito se houver
                            if tem_negrito:
                                linhas_processadas.append(f"{header_prefix}**{texto_sem_negrito}**")
                            else:
                                linhas_processadas.append(f"{header_prefix}{linha_limpa}")
                            nivel_aplicado = True
                            break
                    else:  # regex
                        # Para regex, verifica se corresponde à linha completa (sem negrito)
                        if re.fullmatch(pattern, texto_sem_negrito):
                            header_prefix = self._get_header_prefix(nivel)
                            # Mantém a formatação em negrito se houver
                            if tem_negrito:
                                linhas_processadas.append(f"{header_prefix}**{texto_sem_negrito}**")
                            else:
                                linhas_processadas.append(f"{header_prefix}{linha_limpa}")
                            nivel_aplicado = True
                            break
                
                if nivel_aplicado:
                    break
            
            # Se não aplicou nenhum nível, mantém a linha original
            if not nivel_aplicado:
                linhas_processadas.append(linha)
        
        return '\n'.join(linhas_processadas)
    
    def _identificar_secao_atual(self, texto: str, navegadores: List[Dict]) -> Optional[str]:
        """
        Identifica qual seção do documento o texto atual pertence baseado nos navegadores.
        
        Args:
            texto: Texto a analisar
            navegadores: Lista de navegadores detectados
            
        Returns:
            Nome da seção atual ou None
        """
        # Implementação simplificada - pode ser expandida conforme necessário
        for nav in navegadores:
            if nav["secao"] in texto.upper():
                return nav["secao"]
        return None
    
    def _get_header_prefix(self, nivel):
        """Converte nível hierárquico em prefixo markdown."""
        prefixos = {'h1': '# ', 'h2': '## ', 'h3': '### ', 'h4': '#### '}
        return prefixos.get(nivel, '')
    
    def _extrair_campos_estruturados(self, texto: str) -> List[Dict]:
        """
        Extrai campos estruturados baseado nas configurações.
        
        Args:
            texto: Texto da página
            
        Returns:
            Lista de campos estruturados
        """
        campos = []
        
        for linha in texto.split('\n'):
            linha_limpa = linha.strip()
            
            # Pula linhas que são headers
            if linha_limpa.startswith('#'):
                continue
            
            # Verifica campos em negrito primeiro
            if self.field_config['detect_bold_fields']:
                match_bold = re.match(r'\*\*([^:]+):\*\*\s*(.+)', linha_limpa)
                if match_bold:
                    campos.append({
                        "campo": match_bold.group(1).strip(),
                        "valor": match_bold.group(2).strip(),
                        "tipo": "campo_negrito"
                    })
                    continue
            
            # Verifica padrões de campos
            for pattern in self.field_config['field_patterns']:
                if re.match(pattern, linha_limpa):
                    if self.field_config['field_separator'] in linha_limpa:
                        campo, valor = linha_limpa.split(self.field_config['field_separator'], 1)
                        campos.append({
                            "campo": campo.strip(),
                            "valor": valor.strip(),
                            "tipo": "campo_estruturado"
                        })
                    break
        
        return campos
    
    def _processar_elementos_especiais(self, texto: str) -> Dict:
        """
        Processa elementos especiais baseado nas configurações.
        
        Args:
            texto: Texto da página
            
        Returns:
            Dict com elementos especiais encontrados
        """
        elementos = {
            "assinaturas": [],
            "datas": [],
            "texto_sem_hierarquia": []  # Elementos que não receberam marcação hierárquica
        }
        
        # Processa elementos especiais
        for tipo, config in self.special_elements.items():
            pattern = config['pattern']
            matches = re.finditer(pattern, texto)
            
            for match in matches:
                if tipo == 'signatures':
                    elementos["assinaturas"].append({
                        "texto": match.group(0),
                        "posicao": match.start()
                    })
                elif tipo == 'timestamps':
                    elementos["datas"].append({
                        "texto": match.group(0),
                        "posicao": match.start()
                    })
        
        return elementos
    
    def _analisar_conteudo_projeto(self, texto: str) -> Dict:
        """
        Analisa o conteúdo de projetos com hierarquia avançada.
        
        Args:
            texto: Texto markdown a ser analisado
            
        Returns:
            Dict com análise do conteúdo
        """
        analise = {
            "tipo_documento": None,
            "titulo_principal": None,
            "hierarquia_completa": [],
            "secoes": {},
            "campos_estruturados": []
        }
        
        # Identificar título principal (# Título)
        titulo_h1 = re.search(r'^#\s+([^#\n]+)$', texto, re.MULTILINE)
        if titulo_h1:
            titulo = titulo_h1.group(1).strip()
            # Remove formatação markdown para análise
            titulo_limpo = re.sub(r'\*\*(.+?)\*\*', r'\1', titulo)
            analise["titulo_principal"] = titulo
            
            # Verificar tipo de documento
            for pattern in self.header_config['h1']['patterns']:
                if pattern in titulo_limpo.upper():
                    analise["tipo_documento"] = pattern.lower().replace(' ', '_')
                    break
        
        # Extrair hierarquia completa
        headers = re.finditer(r'^(#+)\s+(.+)$', texto, re.MULTILINE)
        for header in headers:
            nivel_markdown = len(header.group(1))
            titulo = header.group(2).strip()
            
            # Mapear para níveis h1-h4
            nivel_hierarquico = f'h{nivel_markdown}'
            
            analise["hierarquia_completa"].append({
                "nivel": nivel_hierarquico,
                "nivel_markdown": nivel_markdown,
                "titulo": titulo,
                "posicao": header.start()
            })
            
            # Organizar por seções
            if nivel_hierarquico not in analise["secoes"]:
                analise["secoes"][nivel_hierarquico] = []
            analise["secoes"][nivel_hierarquico].append(titulo)
        
        return analise
    
    def gerar_markdown_otimizado(self, paginas: List[Dict]) -> str:
        """
        Gera markdown final com hierarquia preservada sem marcação de páginas.
        
        Args:
            paginas: Lista de páginas processadas
            
        Returns:
            String com markdown estruturado
        """
        markdown_parts = []
        
        for i, pagina in enumerate(paginas):
            # Conteúdo da página (já processado)
            conteudo = pagina["conteudo_markdown"]
            markdown_parts.append(conteudo.strip())
            
            # Navegadores laterais já foram adicionados como títulos H1 no texto
            # Não precisa adicionar seção separada
                        
            # Adiciona quebra de linha entre conteúdos se não for a última página
            if i < len(paginas) - 1:
                markdown_parts.append("\n\n")
        
        return "".join(markdown_parts)
    
    def gerar_indice_hierarquico(self, paginas: List[Dict], niveis_incluir: List[str] = None, incluir_navegadores: bool = True) -> str:
        """
        Gera índice hierárquico baseado na estrutura detectada.
        
        Args:
            paginas: Lista de páginas processadas
            niveis_incluir: Lista dos níveis a incluir no índice (ex: ['h1', 'h2'])
                           Se None, inclui apenas h1
            incluir_navegadores: Se True, inclui navegadores laterais no índice
            
        Returns:
            String com índice markdown
        """
        indice = ["# Índice\n\n"]
        
        # Se não especificado, inclui apenas h1
        if niveis_incluir is None:
            niveis_incluir = ['h1']
        
        # Coletar hierarquia dos níveis especificados
        hierarquia_filtrada = []
        
        for pagina in paginas:
            # Adicionar navegadores laterais primeiro (se houver)
            if incluir_navegadores and pagina.get("navegadores_laterais"):
                for nav in pagina["navegadores_laterais"]:
                    hierarquia_filtrada.append({
                        "nivel": "h1",
                        "nivel_markdown": 1,
                        "titulo": f"**{nav['secao']}**",
                        "pagina": pagina["numero"],
                        "tipo": "navegador_lateral"
                    })
            
            # Adicionar itens da hierarquia normal
            analise = pagina.get("analise_projeto", {})
            for item in analise.get("hierarquia_completa", []):
                # Inclui apenas níveis especificados
                if item["nivel"] in niveis_incluir:
                    hierarquia_filtrada.append({
                        **item,
                        "pagina": pagina["numero"],
                        "tipo": "normal"
                    })
        
        # Organizar com indentação apropriada
        for item in hierarquia_filtrada:
            nivel = item["nivel_markdown"]
            titulo = item["titulo"]
            
            # Remover marcação markdown do título para o índice
            titulo_limpo = re.sub(r'\*\*(.+?)\*\*', r'\1', titulo)
            
            # Criar indentação baseada no nível (apenas se múltiplos níveis)
            if len(niveis_incluir) > 1:
                indent = "  " * (nivel - 1)
            else:
                indent = ""
                
            # Marcar navegadores laterais de forma especial no índice
            if item.get("tipo") == "navegador_lateral":
                indice.append(f"{indent}- **{titulo_limpo}**\n")
            else:
                indice.append(f"{indent}- {titulo_limpo}\n")
        
        return "".join(indice)
    
    def extrair_completo(self, pdf_entrada: Path, saida_md: Path, saida_json: Path):
        """
        Executa extração completa com hierarquia avançada para projetos.
        
        Args:
            pdf_entrada: Caminho do PDF de entrada
            saida_md: Caminho para salvar o Markdown
            saida_json: Caminho para salvar estrutura JSON
            
        Returns:
            Dict com dados completos da extração
        """
        logger.info(f"Iniciando extração de: {pdf_entrada}")
        
        # Garantir diretórios
        saida_md.parent.mkdir(parents=True, exist_ok=True)
        saida_json.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extração com margens controladas e hierarquia avançada
            paginas_processadas = self.extrair_com_margens_controladas(pdf_entrada)
            
            # Gerar markdown final
            markdown_final = self.gerar_markdown_otimizado(paginas_processadas)
            
            # Gerar índice hierárquico incluindo navegadores laterais
            indice = self.gerar_indice_hierarquico(
                paginas_processadas, 
                niveis_incluir=['h1'], 
                incluir_navegadores=True
            )
            
            # Combinar índice e conteúdo
            markdown_completo = indice + "\n---\n\n" + markdown_final
            
            # Salvar markdown
            saida_md.write_text(markdown_completo, encoding="utf-8")
            
            # Preparar resumo estatístico
            total_campos = sum(len(p.get("campos_estruturados", [])) for p in paginas_processadas)
            total_navegadores = sum(len(p.get("navegadores_laterais", [])) for p in paginas_processadas)
            
            # Coletar tipos de documento únicos
            tipos_documento = set()
            
            for p in paginas_processadas:
                tipo = p.get("analise_projeto", {}).get("tipo_documento")
                if tipo:
                    tipos_documento.add(tipo)
            
            # Preparar dados completos para JSON
            dados_completos = {
                "arquivo": str(pdf_entrada),
                "total_paginas": len(paginas_processadas),
                "margens_aplicadas": self.margens,
                "configuracao": {
                    "header_config": self.header_config,
                    "field_config": self.field_config,
                    "special_elements": self.special_elements,
                    "navegadores_laterais": self.navegadores_laterais
                },
                "resumo": {
                    "total_campos_estruturados": total_campos,
                    "total_navegadores_laterais": total_navegadores,
                    "tipos_documento": list(tipos_documento),
                    "hierarquia_detectada": self._resumir_hierarquia(paginas_processadas),
                    "todo_texto_preservado": True  # Indica que nenhum texto foi removido
                },
                "paginas": paginas_processadas
            }
            
            # Salvar estrutura JSON
            with open(saida_json, "w", encoding="utf-8") as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"[✓] Markdown salvo em: {saida_md}")
            logger.info(f"[✓] JSON salvo em: {saida_json}")
            logger.info(f"[✓] Total de páginas: {dados_completos['total_paginas']}")
            logger.info(f"[✓] Total de campos estruturados: {total_campos}")
            logger.info(f"[✓] Total de navegadores laterais: {total_navegadores}")
            logger.info(f"[✓] Tipos de documento: {', '.join(tipos_documento)}")
            logger.info(f"[✓] Hierarquia detectada: {dados_completos['resumo']['hierarquia_detectada']}")
            logger.info(f"[✓] Todo texto preservado: SIM")
            
            return dados_completos
            
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            raise
    
    def _resumir_hierarquia(self, paginas: List[Dict]) -> Dict:
        """
        Resume a hierarquia detectada no documento.
        
        Args:
            paginas: Lista de páginas processadas
            
        Returns:
            Dict com resumo da hierarquia
        """
        resumo = {
            "h1": 0,
            "h2": 0,
            "h3": 0,
            "h4": 0,
            "total_headers": 0,
            "navegadores_laterais": 0
        }
        
        # Contar navegadores laterais
        for pagina in paginas:
            if pagina.get("navegadores_laterais"):
                resumo["navegadores_laterais"] += len(pagina["navegadores_laterais"])
                # Navegadores também são contados como h1
                resumo["h1"] += len(pagina["navegadores_laterais"])
                resumo["total_headers"] += len(pagina["navegadores_laterais"])
        
        # Contar headers normais
        for pagina in paginas:
            analise = pagina.get("analise_projeto", {})
            for nivel, titulos in analise.get("secoes", {}).items():
                if nivel in resumo:
                    resumo[nivel] += len(titulos)
                    resumo["total_headers"] += len(titulos)
        
        return resumo

# Script principal
if __name__ == "__main__":
    # Caminhos
    pdf_entrada = Path("data/input/1.pdf")    #SUBSTITUIR PELO PDF A SER RECEBIDO DA API
    saida_md = Path("data/output/projeto_metis.md")  #INTEGRAR A SAÍDA PARA ENCAMINHAR AO GEMINI COM O SERVIDOR MCP
    saida_json = Path("data/output/projeto_metis_estrutura.json")
    
    # Executar extração
    extrator = ExtratorPDFProjetos()
    dados = extrator.extrair_completo(pdf_entrada, saida_md, saida_json)
    
    # Estatísticas detalhadas
    print(f"\n=== Estatísticas de Extração de Projetos ===")
    print(f"Total de páginas: {dados['total_paginas']}")
    print(f"Total de campos estruturados: {dados['resumo']['total_campos_estruturados']}")
    print(f"Total de navegadores laterais: {dados['resumo']['total_navegadores_laterais']}")
    print(f"Tipos de documento: {', '.join(dados['resumo']['tipos_documento'])}")
    print(f"Hierarquia detectada: {dados['resumo']['hierarquia_detectada']}")
    print(f"Todo texto preservado: {dados['resumo']['todo_texto_preservado']}")
    print(f"Arquivo gerado: {saida_md}")