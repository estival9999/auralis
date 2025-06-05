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
from .busca_local import BuscaSemanticaLocal

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
        
        # Inicializar busca semântica local
        self.busca_semantica = BuscaSemanticaLocal(self.supabase)
        
        # Prompt sistema aprimorado
        self.system_prompt = """Você é um assistente de reuniões corporativas. Seja CONCISO e NATURAL.

REGRAS CRÍTICAS:
1. Para saudações (olá, oi, bom dia): responda APENAS com uma saudação breve e pergunte como pode ajudar
2. Para perguntas vagas: peça esclarecimento de forma educada
3. Para perguntas específicas: responda diretamente ao que foi perguntado
4. NUNCA despeje informações não solicitadas
5. Mantenha respostas curtas a menos que seja pedido detalhamento

Suas capacidades:
- Buscar informações específicas de reuniões quando perguntado
- Responder sobre decisões, participantes, problemas discutidos
- Fornecer resumos quando solicitado

IMPORTANTE: Seja conversacional e natural. Não pareça um robô que despeja informações.

Ao receber uma pergunta:
- Identifique exatamente o que está sendo perguntado
- Busque nos contextos fornecidos
- Se não encontrar exatamente, procure informações relacionadas
- Conecte informações de diferentes reuniões quando relevante
- Responda de forma objetiva e útil"""

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
        """Busca chunks mais relevantes usando busca semântica local"""
        try:
            # Tentar primeiro com threshold padrão
            resultados = self.busca_semantica.buscar_similares(
                query_embedding=embedding_pergunta,
                threshold=0.7,
                limit=num_resultados
            )
            
            # Se não encontrar resultados suficientes, reduzir threshold
            if not resultados or len(resultados) < 2:
                print("Poucos resultados com threshold 0.7, tentando com 0.5...")
                resultados = self.busca_semantica.buscar_similares(
                    query_embedding=embedding_pergunta,
                    threshold=0.5,
                    limit=num_resultados
                )
            
            return resultados
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
        
        # Detectar saudações simples
        saudacoes = ['olá', 'ola', 'oi', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'e aí', 'e ai']
        pergunta_lower = pergunta.lower().strip()
        
        if pergunta_lower in saudacoes:
            return "Olá! Como posso ajudá-lo com informações sobre as reuniões?"
        
        # Detectar perguntas muito vagas
        if len(pergunta_lower.split()) <= 2 and pergunta_lower not in ['resumo', 'decisões', 'participantes', 'problemas']:
            if 'que' in pergunta_lower or 'o que' in pergunta_lower:
                return "Desculpe, não entendi. Você gostaria de saber sobre decisões, participantes, problemas discutidos ou um resumo das reuniões?"
        
        # Analisar pergunta
        analise = self.analisar_pergunta(pergunta)
        print(f"Análise: {analise}")
        
        # Gerar embedding
        embedding_pergunta = self.gerar_embedding_pergunta(pergunta)
        
        # Buscar chunks relevantes
        num_resultados = 8 if analise.get('busca_conexoes', False) else 5
        chunks_relevantes = self.buscar_chunks_relevantes(embedding_pergunta, num_resultados)
        
        if not chunks_relevantes:
            # Tentar buscar chunks mais recentes como fallback
            print("Nenhum chunk relevante encontrado, buscando chunks recentes...")
            try:
                chunks_recentes = self.supabase.table('reunioes_embbed').select(
                    'id, chunk_texto, arquivo_origem, data_reuniao'
                ).order('created_at', desc=True).limit(3).execute()
                
                if chunks_recentes.data:
                    # Adicionar similaridade baixa para indicar que é fallback
                    for chunk in chunks_recentes.data:
                        chunk['similarity'] = 0.4
                    chunks_relevantes = chunks_recentes.data
                else:
                    return "Desculpe, não há informações de reuniões disponíveis no momento."
            except:
                return "Erro ao acessar as informações de reuniões."
        
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
        
        prompt = f"""Responda de forma CONCISA e DIRETA.
{instrucoes_extras}

REGRAS:
1. Seja breve - máximo 2-3 frases a menos que seja pedido mais detalhes
2. Vá direto ao ponto
3. Use linguagem natural e conversacional
4. Se não souber, diga brevemente e sugira o que você pode informar

CONTEXTO DAS REUNIÕES:
{contexto}

PERGUNTA: {pergunta}

Resposta concisa:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Reduzir para respostas mais focadas
                max_tokens=150  # Limitar tamanho da resposta
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