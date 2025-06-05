"""
Sistema de processamento de embeddings para reuniões
Transforma arquivos de texto em embeddings e salva no Supabase
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import hashlib

from openai import OpenAI
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class ProcessadorEmbeddings:
    def __init__(self):
        # Configurar OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no .env")
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Configurar Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Credenciais Supabase não encontradas no .env")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Configurações de chunking
        self.chunk_size = 500  # palavras por chunk
        self.chunk_overlap = 50  # palavras de sobreposição
        
    def criar_chunks_inteligentes(self, texto: str) -> List[Dict[str, any]]:
        """
        Cria chunks inteligentes do texto, preservando contexto
        """
        # Limpar e normalizar texto
        texto = texto.strip()
        
        # Dividir em sentenças
        sentencas = re.split(r'(?<=[.!?])\s+', texto)
        
        chunks = []
        chunk_atual = []
        palavras_no_chunk = 0
        
        for sentenca in sentencas:
            palavras_sentenca = len(sentenca.split())
            
            # Se adicionar essa sentença exceder o tamanho do chunk
            if palavras_no_chunk + palavras_sentenca > self.chunk_size and chunk_atual:
                # Criar chunk
                chunk_texto = ' '.join(chunk_atual)
                chunks.append({
                    'texto': chunk_texto,
                    'numero': len(chunks) + 1
                })
                
                # Manter overlap - pegar últimas sentenças
                palavras_overlap = 0
                chunk_overlap = []
                for i in range(len(chunk_atual) - 1, -1, -1):
                    sent_palavras = len(chunk_atual[i].split())
                    if palavras_overlap + sent_palavras <= self.chunk_overlap:
                        chunk_overlap.insert(0, chunk_atual[i])
                        palavras_overlap += sent_palavras
                    else:
                        break
                
                chunk_atual = chunk_overlap
                palavras_no_chunk = palavras_overlap
            
            chunk_atual.append(sentenca)
            palavras_no_chunk += palavras_sentenca
        
        # Adicionar último chunk
        if chunk_atual:
            chunk_texto = ' '.join(chunk_atual)
            chunks.append({
                'texto': chunk_texto,
                'numero': len(chunks) + 1
            })
        
        return chunks
    
    def extrair_metadados_completos(self, texto: str, nome_arquivo: str) -> Dict:
        """
        Extrai metadados completos incluindo cabeçalho
        """
        metadados = {}
        linhas = texto.split('\n')
        
        # Extrair informações do cabeçalho
        for i, linha in enumerate(linhas[:10]):
            if linha.startswith('Título:'):
                metadados['titulo'] = linha.replace('Título:', '').strip()
            elif linha.startswith('Responsável:'):
                metadados['responsavel'] = linha.replace('Responsável:', '').strip()
            elif linha.startswith('Data:'):
                data_str = linha.replace('Data:', '').strip()
                # Converter formato DD/MM/YYYY para YYYY-MM-DD
                try:
                    from datetime import datetime as dt
                    data_obj = dt.strptime(data_str, '%d/%m/%Y')
                    metadados['data_reuniao'] = data_obj.date()
                except:
                    # Tentar extrair do nome do arquivo como fallback
                    data_match = re.search(r'(\d{4})(\d{2})(\d{2})', nome_arquivo)
                    if data_match:
                        ano, mes, dia = data_match.groups()
                        try:
                            metadados['data_reuniao'] = datetime(int(ano), int(mes), int(dia)).date()
                        except:
                            pass
            elif linha.startswith('Hora:'):
                metadados['hora_inicio'] = linha.replace('Hora:', '').strip()
            elif linha.startswith('Observações:'):
                metadados['observacoes'] = linha.replace('Observações:', '').strip()
        
        # Extrair participantes mencionados no texto
        participantes = []
        for linha in linhas:
            # Procurar por padrões como "João disse:", "Maria respondeu:"
            match = re.match(r'^([A-Z][a-záêçõ]+(?:\s+[A-Z][a-záêçõ]+)*)\s*(?:disse|respondeu|comentou|afirmou|perguntou):', linha)
            if match:
                participantes.append(match.group(1))
        
        # Adicionar participantes únicos
        if participantes:
            metadados['participantes'] = list(set(participantes))[:10]
        
        # Extrair temas principais
        texto_sem_cabecalho = '\n'.join(linhas[10:])  # Pular cabeçalho
        palavras = re.findall(r'\b\w{4,}\b', texto_sem_cabecalho.lower())
        palavras_comuns = ['para', 'pela', 'pelo', 'como', 'quando', 'onde', 'porque', 
                          'então', 'assim', 'depois', 'antes', 'título', 'data', 
                          'hora', 'responsável', 'observações']
        palavras_filtradas = [p for p in palavras if p not in palavras_comuns]
        
        from collections import Counter
        freq_palavras = Counter(palavras_filtradas)
        temas = [palavra for palavra, _ in freq_palavras.most_common(5)]
        if temas:
            metadados['temas'] = temas
        
        return metadados
    
    def gerar_embedding(self, texto: str) -> List[float]:
        """
        Gera embedding usando OpenAI
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro ao gerar embedding: {e}")
            raise
    
    def processar_arquivo(self, caminho_arquivo: str) -> bool:
        """
        Processa um arquivo de reunião completo
        
        Returns:
            bool: True se processado com sucesso
        """
        print(f"Processando arquivo: {caminho_arquivo}")
        
        # Ler arquivo
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                texto_completo = f.read()
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
            return False
        
        if not texto_completo.strip():
            print("Arquivo vazio, pulando...")
            return False
        
        nome_arquivo = Path(caminho_arquivo).name
        
        # Extrair metadados completos do cabeçalho
        metadados = self.extrair_metadados_completos(texto_completo, nome_arquivo)
        
        # Extrair campos específicos
        titulo = metadados.get('titulo', '')
        responsavel = metadados.get('responsavel', '')
        data_reuniao = metadados.get('data_reuniao')
        hora_inicio = metadados.get('hora_inicio', '')
        observacoes = metadados.get('observacoes', '')
        
        # Criar chunks
        chunks = self.criar_chunks_inteligentes(texto_completo)
        print(f"Criados {len(chunks)} chunks")
        
        # Processar cada chunk
        chunks_processados = 0
        for chunk in chunks:
            try:
                # Gerar embedding
                embedding = self.gerar_embedding(chunk['texto'])
                
                # Preparar dados para inserção
                # Converter data para string nos metadados
                metadados_json = metadados.copy()
                if 'data_reuniao' in metadados_json:
                    metadados_json['data_reuniao'] = str(metadados_json['data_reuniao'])
                
                # Converter embedding para JSONB
                import json
                embedding_jsonb = json.dumps(embedding)
                
                dados = {
                    'arquivo_origem': nome_arquivo,
                    'chunk_numero': chunk['numero'],
                    'chunk_texto': chunk['texto'],
                    'embedding': embedding,  # Mantém para compatibilidade
                    'embedding_jsonb': embedding_jsonb,  # Nova coluna JSONB
                    'metadados': metadados_json,
                    'titulo': titulo,
                    'responsavel': responsavel,
                    'observacoes': observacoes
                }
                
                if data_reuniao:
                    dados['data_reuniao'] = str(data_reuniao)
                
                if hora_inicio:
                    dados['hora_inicio'] = hora_inicio
                
                # Inserir no Supabase
                resultado = self.supabase.table('reunioes_embbed').insert(dados).execute()
                print(f"Chunk {chunk['numero']} inserido com sucesso")
                chunks_processados += 1
                
            except Exception as e:
                print(f"Erro ao processar chunk {chunk['numero']}: {e}")
        
        # Retornar True se pelo menos um chunk foi processado
        return chunks_processados > 0
    
    def processar_pasta(self, caminho_pasta: str):
        """
        Processa todos os arquivos .txt em uma pasta
        """
        pasta = Path(caminho_pasta)
        if not pasta.exists():
            print(f"Pasta não encontrada: {caminho_pasta}")
            return
        
        arquivos_txt = list(pasta.glob("*.txt"))
        print(f"Encontrados {len(arquivos_txt)} arquivos .txt")
        
        for arquivo in arquivos_txt:
            self.processar_arquivo(str(arquivo))
        
        print("Processamento concluído!")

# Função auxiliar para verificar arquivos já processados
def verificar_arquivo_processado(supabase: Client, nome_arquivo: str) -> bool:
    """
    Verifica se um arquivo já foi processado
    """
    try:
        resultado = supabase.table('reunioes_embbed').select('id').eq('arquivo_origem', nome_arquivo).limit(1).execute()
        return len(resultado.data) > 0
    except:
        return False

if __name__ == "__main__":
    # Teste do processador
    processador = ProcessadorEmbeddings()
    
    # Processar pasta teste_reuniao
    pasta_reunioes = "/home/mateus/Área de trabalho/DOZERO/teste_reuniao"
    if os.path.exists(pasta_reunioes):
        processador.processar_pasta(pasta_reunioes)
    else:
        print(f"Pasta {pasta_reunioes} não encontrada")