#!/usr/bin/env python3
"""
Script para importar arquivos TXT para o histórico de reuniões do AURALIS
Lê arquivos da pasta update_historico/ e insere no Supabase
"""
import os
import sys
import asyncio
import re
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# Adicionar diretórios ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import UPDATE_HISTORICO_DIR, LOG_FORMAT, LOG_LEVEL
from src.database.supabase_client import supabase_client

# Configurar logging
logger.remove()
logger.add(sys.stderr, format=LOG_FORMAT, level=LOG_LEVEL)

class ImportadorHistorico:
    """Importa transcrições de reuniões para o histórico"""
    
    def __init__(self):
        self.pasta_origem = UPDATE_HISTORICO_DIR
        self.reunioes_processadas = []
        self.erros = []
    
    async def importar_arquivos(self):
        """Processa todos os arquivos TXT da pasta"""
        logger.info(f"Iniciando importação de reuniões de: {self.pasta_origem}")
        
        # Verificar se pasta existe
        if not self.pasta_origem.exists():
            logger.error(f"Pasta não encontrada: {self.pasta_origem}")
            return
        
        # Listar arquivos TXT
        arquivos_txt = list(self.pasta_origem.glob("*.txt"))
        
        if not arquivos_txt:
            logger.warning("Nenhum arquivo TXT encontrado para importar")
            return
        
        logger.info(f"Encontrados {len(arquivos_txt)} arquivos para processar")
        
        # Processar cada arquivo
        for arquivo in arquivos_txt:
            await self.processar_reuniao(arquivo)
        
        # Relatório final
        self.exibir_relatorio()
    
    async def processar_reuniao(self, arquivo_path: Path):
        """Processa arquivo de reunião"""
        try:
            logger.info(f"Processando reunião: {arquivo_path.name}")
            
            # Ler conteúdo
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            if not conteudo.strip():
                logger.warning(f"Arquivo vazio: {arquivo_path.name}")
                return
            
            # Extrair informações da reunião
            dados_reuniao = self.extrair_dados_reuniao(arquivo_path.name, conteudo)
            
            if not dados_reuniao:
                logger.error(f"Não foi possível extrair dados de: {arquivo_path.name}")
                self.erros.append(f"Dados inválidos: {arquivo_path.name}")
                return
            
            # Inserir no banco
            meeting_id = await supabase_client.insert_meeting(dados_reuniao)
            
            if meeting_id:
                self.reunioes_processadas.append({
                    'arquivo': arquivo_path.name,
                    'titulo': dados_reuniao['titulo'],
                    'id': meeting_id
                })
                logger.success(f"✓ Reunião importada: {dados_reuniao['titulo']}")
                
                # Mover para pasta de processados
                await self.mover_para_processados(arquivo_path)
            else:
                self.erros.append(f"Erro ao importar: {arquivo_path.name}")
                logger.error(f"✗ Falha ao importar reunião: {arquivo_path.name}")
                
        except Exception as e:
            erro_msg = f"Erro ao processar {arquivo_path.name}: {str(e)}"
            self.erros.append(erro_msg)
            logger.error(erro_msg)
    
    def extrair_dados_reuniao(self, nome_arquivo: str, conteudo: str) -> dict:
        """Extrai dados estruturados da transcrição"""
        dados = {}
        
        try:
            # Tentar extrair do formato estruturado
            if "📋 **RESUMO EXECUTIVO:**" in conteudo:
                dados = self.extrair_formato_estruturado(conteudo)
            else:
                # Formato livre - extrair o que for possível
                dados = self.extrair_formato_livre(nome_arquivo, conteudo)
            
            # Adicionar dados padrão se não encontrados
            if not dados.get('titulo'):
                dados['titulo'] = nome_arquivo.replace('.txt', '')
            
            if not dados.get('data_reuniao'):
                # Tentar extrair data do nome do arquivo
                data = self.extrair_data_nome(nome_arquivo)
                dados['data_reuniao'] = data or datetime.now().isoformat()
            
            if not dados.get('duracao'):
                # Estimar duração baseada no tamanho do texto
                palavras = len(conteudo.split())
                dados['duracao'] = max(5, palavras // 150)  # ~150 palavras/minuto
            
            return dados
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return None
    
    def extrair_formato_estruturado(self, conteudo: str) -> dict:
        """Extrai dados do formato estruturado padrão"""
        dados = {
            'transcricao_completa': conteudo,
            'decisoes': [],
            'acoes': [],
            'pendencias': [],
            'insights': []
        }
        
        # Extrair seções usando regex
        patterns = {
            'resumo_executivo': r'📋 \*\*RESUMO EXECUTIVO:\*\* (.+?)(?=🎯|\n\n)',
            'decisoes': r'🎯 \*\*DECISÕES TOMADAS:\*\* (.+?)(?=✅|\n\n)',
            'acoes': r'✅ \*\*AÇÕES DEFINIDAS:\*\* (.+?)(?=⚠️|\n\n)', 
            'pendencias': r'⚠️ \*\*PENDÊNCIAS/BLOQUEIOS:\*\* (.+?)(?=📊|\n\n)',
            'insights': r'📊 \*\*INSIGHTS DA EQUIPE:\*\* (.+?)(?=📄|\n\n)'
        }
        
        for campo, pattern in patterns.items():
            match = re.search(pattern, conteudo, re.DOTALL)
            if match:
                texto = match.group(1).strip()
                
                if campo == 'resumo_executivo':
                    dados[campo] = texto
                else:
                    # Processar listas
                    items = re.findall(r'• (.+?)(?=\n|$)', texto)
                    
                    if campo == 'decisoes':
                        for item in items:
                            partes = item.split(' - ')
                            dados['decisoes'].append({
                                'decisao': partes[0].strip() if partes else item,
                                'responsavel': partes[1].replace('Responsável:', '').strip() if len(partes) > 1 else '',
                                'prazo': partes[2].replace('Prazo:', '').strip() if len(partes) > 2 else ''
                            })
                    
                    elif campo == 'acoes':
                        for item in items:
                            partes = item.split(' - ')
                            dados['acoes'].append({
                                'acao': partes[0].strip() if partes else item,
                                'responsavel': partes[1].strip() if len(partes) > 1 else '',
                                'prazo': partes[2].strip() if len(partes) > 2 else ''
                            })
                    
                    else:
                        dados[campo] = [{'item': item} for item in items]
        
        # Extrair título e metadata
        titulo_match = re.search(r'^(.+?) - (\d{2}/\d{2}/\d{4} \d{2}:\d{2}) - (.+?)$', 
                                conteudo.split('\n')[0], re.MULTILINE)
        if titulo_match:
            dados['titulo'] = titulo_match.group(1)
            dados['data_reuniao'] = self.converter_data(titulo_match.group(2))
            dados['responsavel'] = titulo_match.group(3)
        
        return dados
    
    def extrair_formato_livre(self, nome_arquivo: str, conteudo: str) -> dict:
        """Extrai dados de formato não estruturado"""
        dados = {
            'titulo': nome_arquivo.replace('.txt', '').replace('_', ' ').title(),
            'transcricao_completa': conteudo,
            'resumo_executivo': self.gerar_resumo_simples(conteudo),
            'decisoes': [],
            'acoes': [],
            'pendencias': [],
            'insights': []
        }
        
        # Tentar identificar responsável
        responsavel_match = re.search(r'(?:responsável|coordenador|líder|gerente):\s*(.+?)(?:\n|$)', 
                                     conteudo, re.IGNORECASE)
        if responsavel_match:
            dados['responsavel'] = responsavel_match.group(1).strip()
        else:
            dados['responsavel'] = 'Não identificado'
        
        # Identificar área
        area_match = re.search(r'(?:área|departamento|setor):\s*(.+?)(?:\n|$)', 
                              conteudo, re.IGNORECASE)
        if area_match:
            dados['area'] = area_match.group(1).strip()
        
        # Buscar decisões mencionadas
        decisoes = re.findall(r'(?:decidiu-se|ficou decidido|decisão):\s*(.+?)(?:\.|;|\n)', 
                             conteudo, re.IGNORECASE)
        for decisao in decisoes[:5]:  # Limitar a 5
            dados['decisoes'].append({'decisao': decisao.strip()})
        
        # Buscar ações
        acoes = re.findall(r'(?:ação|tarefa|fazer):\s*(.+?)(?:\.|;|\n)', 
                          conteudo, re.IGNORECASE)
        for acao in acoes[:5]:
            dados['acoes'].append({'acao': acao.strip()})
        
        return dados
    
    def gerar_resumo_simples(self, conteudo: str) -> str:
        """Gera resumo simples do conteúdo"""
        # Pegar primeiras 3 frases significativas
        frases = re.split(r'[.!?]\s+', conteudo)
        frases_validas = [f for f in frases if len(f) > 20][:3]
        return ' '.join(frases_validas) + '.'
    
    def extrair_data_nome(self, nome_arquivo: str) -> str:
        """Tenta extrair data do nome do arquivo"""
        # Padrões comuns de data
        padroes = [
            r'(\d{4}[-_]\d{2}[-_]\d{2})',  # YYYY-MM-DD
            r'(\d{2}[-_]\d{2}[-_]\d{4})',  # DD-MM-YYYY
            r'(\d{8})',                     # YYYYMMDD
        ]
        
        for padrao in padroes:
            match = re.search(padrao, nome_arquivo)
            if match:
                data_str = match.group(1).replace('_', '-')
                try:
                    # Tentar diferentes formatos
                    if len(data_str) == 8 and '-' not in data_str:
                        # YYYYMMDD
                        data = datetime.strptime(data_str, '%Y%m%d')
                    elif data_str.count('-') == 2:
                        if data_str.index('-') == 4:
                            # YYYY-MM-DD
                            data = datetime.strptime(data_str, '%Y-%m-%d')
                        else:
                            # DD-MM-YYYY
                            data = datetime.strptime(data_str, '%d-%m-%Y')
                    else:
                        continue
                    
                    return data.isoformat()
                except:
                    continue
        
        return None
    
    def converter_data(self, data_str: str) -> str:
        """Converte string de data para ISO format"""
        try:
            # Formato: DD/MM/YYYY HH:MM
            data = datetime.strptime(data_str, '%d/%m/%Y %H:%M')
            return data.isoformat()
        except:
            return datetime.now().isoformat()
    
    async def mover_para_processados(self, arquivo_path: Path):
        """Move arquivo para pasta de processados"""
        try:
            # Criar pasta de processados se não existir
            pasta_processados = self.pasta_origem / "processados"
            pasta_processados.mkdir(exist_ok=True)
            
            # Mover arquivo
            destino = pasta_processados / arquivo_path.name
            arquivo_path.rename(destino)
            logger.debug(f"Arquivo movido para: {destino}")
            
        except Exception as e:
            logger.warning(f"Não foi possível mover arquivo: {e}")
    
    def exibir_relatorio(self):
        """Exibe relatório final da importação"""
        logger.info("\n" + "="*60)
        logger.info("RELATÓRIO DE IMPORTAÇÃO DE REUNIÕES")
        logger.info("="*60)
        logger.info(f"Total de reuniões processadas: {len(self.reunioes_processadas)}")
        logger.info(f"Sucessos: {len(self.reunioes_processadas)}")
        logger.info(f"Erros: {len(self.erros)}")
        
        if self.reunioes_processadas:
            logger.info("\nReuniões importadas com sucesso:")
            for reuniao in self.reunioes_processadas:
                logger.info(f"  ✓ {reuniao['titulo']} (ID: {reuniao['id'][:8]}...)")
        
        if self.erros:
            logger.error("\nErros encontrados:")
            for erro in self.erros:
                logger.error(f"  ✗ {erro}")
        
        logger.info("="*60 + "\n")

async def main():
    """Função principal"""
    importador = ImportadorHistorico()
    await importador.importar_arquivos()

if __name__ == "__main__":
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║         AURALIS - Importador de Histórico de Reuniões    ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Este script importa transcrições de reuniões da pasta:  ║
    ║  {str(UPDATE_HISTORICO_DIR):^55} ║
    ║                                                           ║
    ║  Os arquivos serão inseridos na tabela historico_reunioes║
    ║  e movidos para a subpasta 'processados' após importação ║
    ║                                                           ║
    ║  Formatos aceitos:                                        ║
    ║  - Formato estruturado com emojis (📋, 🎯, ✅, etc)      ║
    ║  - Formato livre (extração automática)                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    confirmar = input("\nDeseja continuar? (s/n): ")
    if confirmar.lower() == 's':
        asyncio.run(main())
    else:
        print("Importação cancelada.")