"""
Agente de IA melhorado para busca semântica em reuniões
- Prioriza reuniões recentes
- Melhor precisão na busca
- Considera contexto temporal
"""

import os
import re
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime, timedelta

from openai import OpenAI
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class AgenteBuscaMelhorado:
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
        
        # Cache para embeddings
        self._cache_embeddings = {}
        
        # Prompt sistema aprimorado
        self.system_prompt = """Você é um assistente especializado em reuniões corporativas. 

REGRAS CRÍTICAS:
1. Seja CONCISO e DIRETO
2. Para perguntas sobre "última reunião", SEMPRE priorize a mais recente por data/hora
3. Para saudações simples: responda brevemente
4. NUNCA invente informações - use apenas o contexto fornecido
5. Se a informação não estiver disponível, diga claramente

Suas capacidades:
- Buscar informações específicas de reuniões
- Identificar a reunião mais recente
- Responder sobre decisões, participantes, temas
- Fornecer resumos quando solicitado"""

    def detectar_busca_temporal(self, pergunta: str) -> Dict:
        """Detecta se a pergunta busca informações temporais"""
        pergunta_lower = pergunta.lower()
        
        indicadores_recente = ['última', 'ultima', 'mais recente', 'recente', 'últimas', 'ultimas']
        indicadores_primeira = ['primeira', 'mais antiga', 'inicial']
        indicadores_data = ['hoje', 'ontem', 'semana', 'mês', 'mes', 'data', 'quando']
        
        return {
            'busca_recente': any(ind in pergunta_lower for ind in indicadores_recente),
            'busca_primeira': any(ind in pergunta_lower for ind in indicadores_primeira),
            'busca_data': any(ind in pergunta_lower for ind in indicadores_data),
            'tem_contexto_temporal': any([
                any(ind in pergunta_lower for ind in indicadores_recente),
                any(ind in pergunta_lower for ind in indicadores_primeira),
                any(ind in pergunta_lower for ind in indicadores_data)
            ])
        }
    
    def buscar_reuniao_mais_recente(self) -> Optional[Dict]:
        """Busca a reunião mais recente no banco"""
        try:
            # Buscar registros únicos por arquivo, ordenados por data de criação
            resultado = self.supabase.table('reunioes_embbed').select(
                'arquivo_origem, titulo, responsavel, data_reuniao, hora_inicio, created_at, chunk_texto, metadados'
            ).order('created_at', desc=True).limit(10).execute()
            
            if not resultado.data:
                return None
            
            # Agrupar por arquivo e pegar o mais recente
            reunioes_unicas = {}
            for registro in resultado.data:
                arquivo = registro['arquivo_origem']
                if arquivo not in reunioes_unicas:
                    reunioes_unicas[arquivo] = registro
            
            # Retornar a mais recente
            if reunioes_unicas:
                reuniao_mais_recente = list(reunioes_unicas.values())[0]
                return reuniao_mais_recente
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar reunião mais recente: {e}")
            return None
    
    def calcular_similaridade_com_peso_temporal(self, embedding1: List[float], embedding2: List[float], 
                                               data_documento: Optional[str] = None) -> float:
        """Calcula similaridade com peso temporal para priorizar documentos recentes"""
        # Similaridade cosseno básica
        embedding1_np = np.array(embedding1)
        embedding2_np = np.array(embedding2)
        
        similaridade = np.dot(embedding1_np, embedding2_np) / (
            np.linalg.norm(embedding1_np) * np.linalg.norm(embedding2_np)
        )
        
        # Aplicar peso temporal se houver data
        if data_documento:
            try:
                # Parse da data
                if isinstance(data_documento, str):
                    # Tentar diferentes formatos
                    for fmt in ['%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d']:
                        try:
                            data_doc = datetime.strptime(data_documento.replace('+00:00', ''), fmt.replace('%z', ''))
                            break
                        except:
                            continue
                    else:
                        return similaridade
                else:
                    data_doc = data_documento
                
                # Calcular diferença em dias
                dias_diferenca = (datetime.now() - data_doc).days
                
                # Peso temporal (decai com o tempo)
                # Documentos recentes (< 7 dias) recebem boost
                if dias_diferenca < 7:
                    peso_temporal = 1.2
                elif dias_diferenca < 30:
                    peso_temporal = 1.1
                elif dias_diferenca < 90:
                    peso_temporal = 1.0
                else:
                    peso_temporal = 0.9
                
                similaridade *= peso_temporal
                
            except Exception as e:
                print(f"Erro ao calcular peso temporal: {e}")
        
        return min(similaridade, 1.0)  # Garantir que não passe de 1.0
    
    def gerar_embedding_pergunta(self, pergunta: str) -> List[float]:
        """Gera embedding para a pergunta do usuário"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=pergunta
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro ao gerar embedding da pergunta: {e}")
            raise
    
    def buscar_chunks_relevantes(self, pergunta: str, num_resultados: int = 5) -> List[Dict]:
        """Busca chunks relevantes com melhorias"""
        try:
            # Detectar contexto temporal
            contexto_temporal = self.detectar_busca_temporal(pergunta)
            
            # Se busca a última reunião, retornar diretamente
            if contexto_temporal['busca_recente']:
                reuniao_recente = self.buscar_reuniao_mais_recente()
                if reuniao_recente:
                    return [{
                        **reuniao_recente,
                        'similarity': 1.0  # Alta relevância para busca direta
                    }]
            
            # Buscar todos os embeddings
            resultado = self.supabase.table('reunioes_embbed').select('*').execute()
            
            if not resultado.data:
                return []
            
            # Gerar embedding da pergunta
            embedding_pergunta = self.gerar_embedding_pergunta(pergunta)
            
            # Calcular similaridades
            resultados_com_score = []
            for chunk in resultado.data:
                try:
                    # Obter embedding
                    embedding_chunk = chunk.get('embedding', [])
                    
                    # Se for string JSON, converter para array
                    if isinstance(embedding_chunk, str):
                        try:
                            embedding_chunk = json.loads(embedding_chunk)
                        except json.JSONDecodeError:
                            print(f"Erro ao decodificar embedding do chunk {chunk.get('id')}")
                            continue
                    
                    # Verificar dimensões
                    if not embedding_chunk or len(embedding_chunk) != 1536:
                        continue
                    
                    # Calcular similaridade com peso temporal
                    similaridade = self.calcular_similaridade_com_peso_temporal(
                        embedding_pergunta,
                        embedding_chunk,
                        chunk.get('created_at')
                    )
                    
                    chunk['similarity'] = similaridade
                    resultados_com_score.append(chunk)
                    
                except Exception as e:
                    print(f"Erro ao processar chunk {chunk.get('id')}: {e}")
                    continue
            
            # Ordenar por similaridade
            resultados_com_score.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Retornar top N
            return resultados_com_score[:num_resultados]
            
        except Exception as e:
            print(f"Erro ao buscar chunks: {e}")
            return []
    
    def processar_pergunta(self, pergunta: str) -> str:
        """Processa uma pergunta e retorna a resposta"""
        print(f"Processando pergunta: {pergunta}")
        
        # Detectar saudações simples
        saudacoes = ['olá', 'ola', 'oi', 'bom dia', 'boa tarde', 'boa noite']
        pergunta_lower = pergunta.lower().strip()
        
        if pergunta_lower in saudacoes:
            return "Olá! Como posso ajudá-lo com informações sobre as reuniões?"
        
        # Buscar chunks relevantes
        chunks_relevantes = self.buscar_chunks_relevantes(pergunta, num_resultados=5)
        
        if not chunks_relevantes:
            return "Desculpe, não encontrei informações sobre reuniões no sistema."
        
        # Preparar contexto
        contexto = self._preparar_contexto(chunks_relevantes)
        
        # Gerar resposta
        resposta = self._gerar_resposta(pergunta, contexto)
        
        return resposta
    
    def _preparar_contexto(self, chunks: List[Dict]) -> str:
        """Prepara o contexto dos chunks para o LLM"""
        contexto = ""
        reunioes_vistas = set()
        
        for i, chunk in enumerate(chunks):
            # Extrair informações
            arquivo = chunk.get('arquivo_origem', 'Arquivo desconhecido')
            titulo = chunk.get('titulo', chunk.get('metadados', {}).get('titulo', 'Sem título'))
            data = chunk.get('data_reuniao', 'Data não informada')
            hora = chunk.get('hora_inicio', '')
            responsavel = chunk.get('responsavel', '')
            texto = chunk.get('chunk_texto', '')
            similaridade = chunk.get('similarity', 0)
            
            # Identificador único da reunião
            reuniao_id = f"{arquivo}_{data}"
            
            # Adicionar cabeçalho da reunião se for nova
            if reuniao_id not in reunioes_vistas:
                contexto += f"\n\n=== REUNIÃO {i+1}: {titulo} ==="
                contexto += f"\nData: {data}"
                if hora:
                    contexto += f" às {hora}"
                if responsavel:
                    contexto += f"\nResponsável: {responsavel}"
                contexto += f"\nRelevância: {similaridade:.2%}\n"
                reunioes_vistas.add(reuniao_id)
            
            # Adicionar texto do chunk
            contexto += f"\n{texto}\n"
        
        return contexto
    
    def _gerar_resposta(self, pergunta: str, contexto: str) -> str:
        """Gera resposta usando o contexto encontrado"""
        
        # Detectar se é pergunta sobre última reunião
        contexto_temporal = self.detectar_busca_temporal(pergunta)
        
        instrucoes_extras = ""
        if contexto_temporal['busca_recente']:
            instrucoes_extras = "\nIMPORTANTE: A primeira reunião no contexto é a MAIS RECENTE. Responda baseando-se nela."
        
        prompt = f"""Com base no contexto fornecido, responda a pergunta de forma DIRETA e CONCISA.
{instrucoes_extras}

CONTEXTO DAS REUNIÕES:
{contexto}

PERGUNTA: {pergunta}

Resposta (seja direto e específico):"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao processar resposta: {str(e)}"