"""
Processador de Base de Conhecimento
Processa documentos TXT, gera embeddings e armazena no Supabase
Similar ao processamento de reuniões mas otimizado para documentos estáticos
"""

import os
import hashlib
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import re
from pathlib import Path

import numpy as np
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class ProcessadorBaseConhecimento:
    """Processa documentos da base de conhecimento para busca semântica"""
    
    def __init__(self):
        """Inicializa o processador com clientes OpenAI e Supabase"""
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.supabase_client: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        
        # Configurações de chunking
        self.chunk_size = 1500  # Caracteres por chunk
        self.chunk_overlap = 200  # Overlap entre chunks
        self.embedding_model = "text-embedding-ada-002"
        
        print("✅ Processador de Base de Conhecimento inicializado")
    
    def calcular_hash_documento(self, conteudo: str) -> str:
        """Calcula hash SHA256 do documento para controle de versão"""
        return hashlib.sha256(conteudo.encode()).hexdigest()
    
    def limpar_texto(self, texto: str) -> str:
        """Limpa e normaliza o texto do documento"""
        # Remove múltiplos espaços e quebras de linha
        texto = re.sub(r'\s+', ' ', texto)
        # Remove caracteres especiais mantendo pontuação básica
        texto = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]', '', texto)
        return texto.strip()
    
    def criar_chunks(self, texto: str) -> List[Dict[str, any]]:
        """
        Divide o texto em chunks com overlap
        Retorna lista de dicionários com conteúdo e metadados
        """
        chunks = []
        texto_limpo = self.limpar_texto(texto)
        
        # Divide por sentenças para não cortar no meio
        sentencas = re.split(r'(?<=[.!?])\s+', texto_limpo)
        
        chunk_atual = ""
        chunk_index = 0
        
        for sentenca in sentencas:
            # Se adicionar a sentença exceder o tamanho, cria novo chunk
            if len(chunk_atual) + len(sentenca) > self.chunk_size and chunk_atual:
                chunks.append({
                    'conteudo': chunk_atual.strip(),
                    'chunk_index': chunk_index,
                    'chunk_size': len(chunk_atual.strip())
                })
                
                # Overlap: mantém parte do chunk anterior
                palavras_overlap = chunk_atual.split()[-30:]  # ~200 caracteres
                chunk_atual = ' '.join(palavras_overlap) + ' ' + sentenca
                chunk_index += 1
            else:
                chunk_atual += ' ' + sentenca
        
        # Adiciona último chunk se houver
        if chunk_atual.strip():
            chunks.append({
                'conteudo': chunk_atual.strip(),
                'chunk_index': chunk_index,
                'chunk_size': len(chunk_atual.strip())
            })
        
        print(f"📄 Documento dividido em {len(chunks)} chunks")
        return chunks
    
    def gerar_embedding(self, texto: str) -> List[float]:
        """Gera embedding usando OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Erro ao gerar embedding: {e}")
            raise
    
    def detectar_tipo_documento(self, conteudo: str, nome_arquivo: str) -> Tuple[str, str]:
        """
        Detecta o tipo e categoria do documento baseado no conteúdo e nome
        Retorna (tipo_documento, categoria)
        """
        conteudo_lower = conteudo.lower()
        nome_lower = nome_arquivo.lower()
        
        # Detecção por palavras-chave
        if any(palavra in conteudo_lower for palavra in ['manual', 'instruções', 'procedimento operacional']):
            tipo = 'manual'
            if 'técnico' in conteudo_lower:
                categoria = 'manual_tecnico'
            elif 'usuário' in conteudo_lower:
                categoria = 'manual_usuario'
            else:
                categoria = 'manual_geral'
        
        elif any(palavra in conteudo_lower for palavra in ['estatuto', 'regimento', 'regulamento']):
            tipo = 'estatuto'
            categoria = 'estatuto_social'
        
        elif any(palavra in conteudo_lower for palavra in ['procedimento', 'processo', 'fluxo']):
            tipo = 'procedimento'
            if 'qualidade' in conteudo_lower:
                categoria = 'procedimento_qualidade'
            elif 'segurança' in conteudo_lower:
                categoria = 'procedimento_seguranca'
            else:
                categoria = 'procedimento_operacional'
        
        elif any(palavra in conteudo_lower for palavra in ['política', 'diretrizes', 'normas']):
            tipo = 'politica'
            categoria = 'politica_interna'
        
        else:
            tipo = 'documento'
            categoria = 'documento_geral'
        
        return tipo, categoria
    
    def extrair_tags(self, conteudo: str, tipo_documento: str) -> List[str]:
        """Extrai tags relevantes do documento"""
        tags = []
        conteudo_lower = conteudo.lower()
        
        # Tags gerais
        palavras_chave = [
            'qualidade', 'segurança', 'processo', 'gestão', 'controle',
            'auditoria', 'compliance', 'treinamento', 'comunicação',
            'financeiro', 'recursos humanos', 'ti', 'tecnologia',
            'vendas', 'marketing', 'operações', 'logística'
        ]
        
        for palavra in palavras_chave:
            if palavra in conteudo_lower:
                tags.append(palavra)
        
        # Adiciona o tipo como tag
        tags.append(tipo_documento)
        
        # Remove duplicatas
        return list(set(tags))
    
    def processar_documento(self, caminho_arquivo: str, versao: str = "1.0", notas_versao: str = "") -> Dict[str, any]:
        """
        Processa um documento completo:
        1. Lê o arquivo
        2. Cria chunks
        3. Gera embeddings
        4. Salva no Supabase
        """
        print(f"\n🔄 Iniciando processamento de: {caminho_arquivo}")
        
        try:
            # Lê o arquivo
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            if not conteudo.strip():
                raise ValueError("Arquivo vazio")
            
            # Extrai metadados
            nome_arquivo = os.path.basename(caminho_arquivo)
            hash_documento = self.calcular_hash_documento(conteudo)
            tipo_documento, categoria = self.detectar_tipo_documento(conteudo, nome_arquivo)
            tags = self.extrair_tags(conteudo, tipo_documento)
            
            print(f"📋 Tipo: {tipo_documento} | Categoria: {categoria}")
            print(f"🏷️  Tags: {', '.join(tags)}")
            
            # Verifica se documento já existe
            resultado_existente = self.supabase_client.table('base_conhecimento').select('id').eq(
                'hash_documento', hash_documento
            ).execute()
            
            if resultado_existente.data:
                print("⚠️  Documento já processado com este conteúdo")
                return {
                    'status': 'ja_existe',
                    'documento': nome_arquivo,
                    'hash': hash_documento
                }
            
            # Cria chunks
            chunks = self.criar_chunks(conteudo)
            
            # Processa cada chunk
            chunks_salvos = 0
            erros = []
            
            for i, chunk in enumerate(chunks):
                try:
                    print(f"🔄 Processando chunk {i+1}/{len(chunks)}...", end='\r')
                    
                    # Gera embedding
                    embedding = self.gerar_embedding(chunk['conteudo'])
                    
                    # Prepara dados para inserção
                    dados_chunk = {
                        'conteudo': chunk['conteudo'],
                        'embedding': embedding,
                        'chunk_index': chunk['chunk_index'],
                        'chunk_size': chunk['chunk_size'],
                        'documento_origem': nome_arquivo,
                        'tipo_documento': tipo_documento,
                        'categoria': categoria,
                        'tags': tags,
                        'versao_documento': versao,
                        'hash_documento': hash_documento,
                        'metadata': {
                            'processado_em': datetime.now().isoformat(),
                            'total_chunks': len(chunks),
                            'tamanho_original': len(conteudo)
                        }
                    }
                    
                    # Salva no Supabase
                    self.supabase_client.table('base_conhecimento').insert(dados_chunk).execute()
                    chunks_salvos += 1
                    
                except Exception as e:
                    erros.append(f"Chunk {i}: {str(e)}")
                    print(f"\n❌ Erro no chunk {i}: {e}")
            
            print(f"\n✅ {chunks_salvos}/{len(chunks)} chunks salvos com sucesso")
            
            # Registra versão do documento
            try:
                self.supabase_client.table('base_conhecimento_versoes').insert({
                    'documento_origem': nome_arquivo,
                    'versao': versao,
                    'hash_documento': hash_documento,
                    'notas_versao': notas_versao,
                    'usuario_upload': 'sistema'
                }).execute()
            except Exception as e:
                print(f"⚠️  Aviso: Erro ao registrar versão: {e}")
            
            return {
                'status': 'sucesso',
                'documento': nome_arquivo,
                'tipo': tipo_documento,
                'categoria': categoria,
                'tags': tags,
                'chunks_processados': chunks_salvos,
                'total_chunks': len(chunks),
                'hash': hash_documento,
                'erros': erros
            }
            
        except Exception as e:
            print(f"\n❌ Erro ao processar documento: {e}")
            return {
                'status': 'erro',
                'documento': caminho_arquivo,
                'erro': str(e)
            }
    
    def processar_pasta(self, caminho_pasta: str) -> List[Dict[str, any]]:
        """Processa todos os arquivos TXT em uma pasta"""
        resultados = []
        pasta = Path(caminho_pasta)
        
        if not pasta.exists():
            print(f"❌ Pasta não encontrada: {caminho_pasta}")
            return resultados
        
        arquivos_txt = list(pasta.glob("*.txt"))
        
        if not arquivos_txt:
            print(f"⚠️  Nenhum arquivo TXT encontrado em: {caminho_pasta}")
            return resultados
        
        print(f"📁 Encontrados {len(arquivos_txt)} arquivos TXT para processar")
        
        for arquivo in arquivos_txt:
            resultado = self.processar_documento(str(arquivo))
            resultados.append(resultado)
        
        return resultados
    
    def buscar_conhecimento(self, consulta: str, limite: int = 5, filtros: Dict = None) -> List[Dict]:
        """
        Busca conhecimento similar usando embeddings
        """
        try:
            # Gera embedding da consulta
            embedding_consulta = self.gerar_embedding(consulta)
            
            # Prepara parâmetros da função SQL
            params = {
                'query_embedding': embedding_consulta,
                'limite': limite
            }
            
            if filtros:
                if 'tipo_documento' in filtros:
                    params['tipo_doc'] = filtros['tipo_documento']
                if 'categoria' in filtros:
                    params['categoria_filtro'] = filtros['categoria']
                if 'tags' in filtros:
                    params['tags_filtro'] = filtros['tags']
            
            # Chama função SQL
            resultado = self.supabase_client.rpc('buscar_conhecimento_similar', params).execute()
            
            return resultado.data
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def listar_documentos(self) -> List[Dict]:
        """Lista todos os documentos processados"""
        try:
            resultado = self.supabase_client.table('base_conhecimento').select(
                'documento_origem, tipo_documento, categoria, versao_documento'
            ).eq('ativo', True).execute()
            
            # Agrupa por documento único
            documentos = {}
            for item in resultado.data:
                doc = item['documento_origem']
                if doc not in documentos:
                    documentos[doc] = {
                        'documento': doc,
                        'tipo': item['tipo_documento'],
                        'categoria': item['categoria'],
                        'versao': item['versao_documento']
                    }
            
            return list(documentos.values())
            
        except Exception as e:
            print(f"❌ Erro ao listar documentos: {e}")
            return []


# Teste rápido
if __name__ == "__main__":
    processador = ProcessadorBaseConhecimento()
    
    # Teste de chunking
    texto_teste = """Este é um manual de procedimentos da empresa.
    O manual contém instruções detalhadas sobre os processos de qualidade.
    Cada procedimento deve ser seguido rigorosamente para garantir a conformidade.
    Este documento é parte do sistema de gestão da qualidade."""
    
    chunks = processador.criar_chunks(texto_teste)
    print(f"\nTeste de chunking: {len(chunks)} chunks criados")
    
    # Teste de detecção
    tipo, categoria = processador.detectar_tipo_documento(texto_teste, "manual_qualidade.txt")
    print(f"Tipo detectado: {tipo} | Categoria: {categoria}")
    
    # Teste de tags
    tags = processador.extrair_tags(texto_teste, tipo)
    print(f"Tags extraídas: {tags}")