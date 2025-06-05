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

import openai
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
        openai.api_key = self.openai_api_key
        
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
    
    def extrair_metadados(self, texto: str, nome_arquivo: str) -> Dict:
        """
        Extrai metadados do texto e nome do arquivo
        """
        metadados = {}
        
        # Tentar extrair data do nome do arquivo
        data_match = re.search(r'(\d{2})[_-](\d{2})[_-](\d{4})', nome_arquivo)
        if data_match:
            dia, mes, ano = data_match.groups()
            try:
                data_reuniao = datetime(int(ano), int(mes), int(dia))
                metadados['data_reuniao'] = data_reuniao.date()
            except:
                pass
        
        # Identificar possíveis participantes (nomes próprios)
        nomes_proprios = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', texto)
        participantes_unicos = list(set(nomes_proprios))[:10]  # Limitar a 10
        if participantes_unicos:
            metadados['participantes'] = participantes_unicos
        
        # Identificar temas principais (palavras mais frequentes significativas)
        palavras = re.findall(r'\b\w{4,}\b', texto.lower())
        palavras_comuns = ['para', 'pela', 'pelo', 'como', 'quando', 'onde', 'porque', 'então', 'assim', 'depois', 'antes']
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
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=texto
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Erro ao gerar embedding: {e}")
            raise
    
    def processar_arquivo(self, caminho_arquivo: str):
        """
        Processa um arquivo de reunião completo
        """
        print(f"Processando arquivo: {caminho_arquivo}")
        
        # Ler arquivo
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                texto_completo = f.read()
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
            return
        
        if not texto_completo.strip():
            print("Arquivo vazio, pulando...")
            return
        
        nome_arquivo = Path(caminho_arquivo).name
        
        # Extrair metadados
        metadados = self.extrair_metadados(texto_completo, nome_arquivo)
        data_reuniao = metadados.get('data_reuniao')
        
        # Criar chunks
        chunks = self.criar_chunks_inteligentes(texto_completo)
        print(f"Criados {len(chunks)} chunks")
        
        # Processar cada chunk
        for chunk in chunks:
            try:
                # Gerar embedding
                embedding = self.gerar_embedding(chunk['texto'])
                
                # Preparar dados para inserção
                dados = {
                    'arquivo_origem': nome_arquivo,
                    'chunk_numero': chunk['numero'],
                    'chunk_texto': chunk['texto'],
                    'embedding': embedding,
                    'metadados': metadados
                }
                
                if data_reuniao:
                    dados['data_reuniao'] = str(data_reuniao)
                
                # Inserir no Supabase
                resultado = self.supabase.table('reunioes_embbed').insert(dados).execute()
                print(f"Chunk {chunk['numero']} inserido com sucesso")
                
            except Exception as e:
                print(f"Erro ao processar chunk {chunk['numero']}: {e}")
    
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