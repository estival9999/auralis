"""
Agente de IA para busca semântica em reuniões
Interpreta perguntas e busca informações relevantes nos embeddings
"""

import os
import re
from typing import List, Dict, Optional, Tuple
import json

from openai import OpenAI
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class AgenteBuscaReunioes:
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
        
        # Prompt sistema para o agente
        self.system_prompt = """Você é um assistente especializado em analisar informações de reuniões corporativas.

Suas capacidades incluem:
1. Buscar informações específicas (definições, decisões, responsáveis, problemas)
2. Identificar conexões entre diferentes reuniões
3. Fornecer respostas claras e diretas
4. Citar trechos relevantes quando apropriado
5. Informar claramente quando não encontrar informações

Ao receber uma pergunta:
- Identifique exatamente o que está sendo perguntado
- Busque nos contextos fornecidos
- Conecte informações de diferentes reuniões quando relevante
- Responda de forma objetiva e profissional"""

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
    
    def buscar_chunks_relevantes(self, embedding_pergunta: List[float], num_resultados: int = 5) -> List[Dict]:
        """Busca chunks mais relevantes no banco"""
        try:
            # Usar a função SQL criada
            resultado = self.supabase.rpc(
                'buscar_chunks_similares',
                {
                    'query_embedding': embedding_pergunta,
                    'similarity_threshold': 0.7,
                    'match_count': num_resultados
                }
            ).execute()
            
            return resultado.data
        except Exception as e:
            print(f"Erro ao buscar chunks: {e}")
            return []
    
    def analisar_pergunta(self, pergunta: str) -> Dict:
        """Analisa a pergunta para identificar intenção e entidades"""
        prompt = f"""Analise a seguinte pergunta sobre reuniões e identifique:
1. Tipo de informação buscada (decisão, responsável, problema, definição, etc)
2. Entidades mencionadas (pessoas, projetos, datas, etc)
3. Se busca conexões entre reuniões

Pergunta: {pergunta}

Responda em JSON com: tipo_busca, entidades, busca_conexoes (true/false)"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um analisador de perguntas. Responda apenas em JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {
                "tipo_busca": "geral",
                "entidades": [],
                "busca_conexoes": False
            }
    
    def processar_pergunta(self, pergunta: str) -> str:
        """Processa uma pergunta e retorna a resposta"""
        print(f"Processando pergunta: {pergunta}")
        
        # Analisar pergunta
        analise = self.analisar_pergunta(pergunta)
        print(f"Análise: {analise}")
        
        # Gerar embedding
        embedding_pergunta = self.gerar_embedding_pergunta(pergunta)
        
        # Buscar chunks relevantes
        num_resultados = 8 if analise.get('busca_conexoes', False) else 5
        chunks_relevantes = self.buscar_chunks_relevantes(embedding_pergunta, num_resultados)
        
        if not chunks_relevantes:
            return "Desculpe, não encontrei informações relevantes sobre essa pergunta nas reuniões registradas."
        
        # Preparar contexto
        contexto_reunioes = self._preparar_contexto(chunks_relevantes)
        
        # Gerar resposta
        resposta = self._gerar_resposta(pergunta, contexto_reunioes, analise)
        
        return resposta
    
    def _preparar_contexto(self, chunks: List[Dict]) -> str:
        """Prepara o contexto dos chunks para o LLM"""
        contexto = ""
        reunioes_vistas = set()
        
        for chunk in chunks:
            arquivo = chunk.get('arquivo_origem', 'Arquivo desconhecido')
            data = chunk.get('data_reuniao', 'Data não informada')
            texto = chunk.get('chunk_texto', '')
            similaridade = chunk.get('similarity', 0)
            
            # Marcar reunião
            reuniao_id = f"{arquivo}_{data}"
            if reuniao_id not in reunioes_vistas:
                contexto += f"\n\n=== REUNIÃO: {arquivo} ({data}) ===\n"
                reunioes_vistas.add(reuniao_id)
            
            contexto += f"\n[Relevância: {similaridade:.2%}]\n{texto}\n"
        
        return contexto
    
    def _gerar_resposta(self, pergunta: str, contexto: str, analise: Dict) -> str:
        """Gera resposta usando o contexto encontrado"""
        
        # Adicionar instruções específicas baseadas na análise
        instrucoes_extras = ""
        if analise.get('busca_conexoes', False):
            instrucoes_extras = "\nIdentifique e destaque conexões entre diferentes reuniões."
        
        tipo_busca = analise.get('tipo_busca', 'geral')
        if tipo_busca == 'responsável':
            instrucoes_extras += "\nFoque em identificar pessoas responsáveis e suas atribuições."
        elif tipo_busca == 'decisão':
            instrucoes_extras += "\nDestaque as decisões tomadas e seus impactos."
        elif tipo_busca == 'problema':
            instrucoes_extras += "\nIdentifique problemas mencionados e possíveis soluções discutidas."
        
        prompt = f"""Com base no contexto das reuniões abaixo, responda à pergunta do usuário.
{instrucoes_extras}

CONTEXTO DAS REUNIÕES:
{contexto}

PERGUNTA DO USUÁRIO:
{pergunta}

Forneça uma resposta clara e direta. Se não encontrar a informação, diga claramente."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao processar resposta: {str(e)}"
    
    def buscar_conexoes_tematicas(self, tema: str, limite: int = 10) -> List[Dict]:
        """Busca conexões temáticas entre diferentes reuniões"""
        # Gerar embedding do tema
        embedding_tema = self.gerar_embedding_pergunta(f"reuniões sobre {tema}")
        
        # Buscar chunks relacionados
        chunks = self.buscar_chunks_relevantes(embedding_tema, limite)
        
        # Agrupar por reunião
        reunioes_por_arquivo = {}
        for chunk in chunks:
            arquivo = chunk.get('arquivo_origem', 'Desconhecido')
            if arquivo not in reunioes_por_arquivo:
                reunioes_por_arquivo[arquivo] = []
            reunioes_por_arquivo[arquivo].append(chunk)
        
        return reunioes_por_arquivo

# Classe de integração com o FRONT.py
class IntegracaoAssistenteReunioes:
    def __init__(self):
        self.agente = AgenteBuscaReunioes()
    
    def processar_mensagem_usuario(self, mensagem: str) -> str:
        """Interface principal para o FRONT.py"""
        try:
            resposta = self.agente.processar_pergunta(mensagem)
            return resposta
        except Exception as e:
            return f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"

# Funções auxiliares
def testar_agente():
    """Função de teste do agente"""
    agente = AgenteBuscaReunioes()
    
    perguntas_teste = [
        "Quais foram as principais decisões tomadas?",
        "Quem é responsável pelo projeto X?",
        "Quais problemas foram levantados nas reuniões?",
        "Existe alguma conexão entre as reuniões de janeiro e fevereiro?",
        "O que foi definido sobre o orçamento?"
    ]
    
    for pergunta in perguntas_teste:
        print(f"\nPergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta)
        print(f"Resposta: {resposta}")
        print("-" * 80)

if __name__ == "__main__":
    # Testar o agente
    testar_agente()