"""
Versão melhorada do agente de busca com fallbacks inteligentes
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

class AgenteBuscaReunioesAprimorado:
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
        
        # Prompt sistema aprimorado
        self.system_prompt = """Você é um assistente especializado em analisar informações de reuniões corporativas.

Suas capacidades incluem:
1. Buscar informações específicas (definições, decisões, responsáveis, problemas)
2. Identificar conexões entre diferentes reuniões
3. Fornecer respostas claras e diretas
4. Citar trechos relevantes quando apropriado
5. Quando não encontrar informações específicas, fornecer um resumo geral do que está disponível

IMPORTANTE: 
- Se não encontrar a informação exata solicitada, forneça informações relacionadas ou um resumo do que está disponível
- Sempre tente extrair valor do contexto fornecido
- Seja criativo na interpretação das informações disponíveis"""

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
    
    def buscar_chunks_relevantes_multiplos(self, pergunta: str, num_resultados: int = 5) -> List[Dict]:
        """
        Busca chunks usando múltiplas estratégias
        """
        chunks_combinados = []
        chunks_ids = set()
        
        # Estratégia 1: Busca direta com a pergunta original
        try:
            embedding_original = self.gerar_embedding_pergunta(pergunta)
            chunks_diretos = self._buscar_chunks_por_embedding(embedding_original, num_resultados, threshold=0.6)
            
            for chunk in chunks_diretos:
                chunk_id = chunk.get('id')
                if chunk_id and chunk_id not in chunks_ids:
                    chunks_ids.add(chunk_id)
                    chunks_combinados.append(chunk)
        except Exception as e:
            print(f"Erro na busca direta: {e}")
        
        # Estratégia 2: Reformular pergunta para contexto mais específico
        perguntas_reformuladas = self._reformular_pergunta(pergunta)
        
        for pergunta_reformulada in perguntas_reformuladas:
            try:
                embedding_reformulado = self.gerar_embedding_pergunta(pergunta_reformulada)
                chunks_reformulados = self._buscar_chunks_por_embedding(
                    embedding_reformulado, 
                    num_resultados=3, 
                    threshold=0.55
                )
                
                for chunk in chunks_reformulados:
                    chunk_id = chunk.get('id')
                    if chunk_id and chunk_id not in chunks_ids:
                        chunks_ids.add(chunk_id)
                        chunks_combinados.append(chunk)
                        
            except Exception as e:
                print(f"Erro na busca reformulada: {e}")
        
        # Se ainda não tiver chunks suficientes, buscar os mais recentes
        if len(chunks_combinados) < 3:
            try:
                chunks_recentes = self._buscar_chunks_recentes(5)
                for chunk in chunks_recentes:
                    chunk_id = chunk.get('id')
                    if chunk_id and chunk_id not in chunks_ids:
                        chunks_ids.add(chunk_id)
                        chunks_combinados.append(chunk)
                        if len(chunks_combinados) >= num_resultados:
                            break
            except Exception as e:
                print(f"Erro ao buscar chunks recentes: {e}")
        
        # Ordenar por relevância
        chunks_combinados.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return chunks_combinados[:num_resultados]
    
    def _buscar_chunks_por_embedding(self, embedding: List[float], num_resultados: int, threshold: float) -> List[Dict]:
        """Busca chunks usando embedding específico"""
        try:
            resultado = self.supabase.rpc(
                'buscar_chunks_similares',
                {
                    'query_embedding': embedding,
                    'similarity_threshold': threshold,
                    'match_count': num_resultados
                }
            ).execute()
            
            return resultado.data if resultado.data else []
        except Exception as e:
            print(f"Erro ao buscar chunks: {e}")
            return []
    
    def _buscar_chunks_recentes(self, limite: int) -> List[Dict]:
        """Busca os chunks mais recentes como fallback"""
        try:
            resultado = self.supabase.table('reunioes_embbed').select(
                'id, chunk_texto, arquivo_origem, data_reuniao'
            ).order('created_at', desc=True).limit(limite).execute()
            
            # Adicionar similaridade fictícia baixa
            for chunk in resultado.data:
                chunk['similarity'] = 0.5
                
            return resultado.data if resultado.data else []
        except Exception as e:
            print(f"Erro ao buscar chunks recentes: {e}")
            return []
    
    def _reformular_pergunta(self, pergunta: str) -> List[str]:
        """Reformula a pergunta para melhorar a busca semântica"""
        reformulacoes = []
        
        pergunta_lower = pergunta.lower()
        
        # Mapeamentos específicos
        if "quem participou" in pergunta_lower or "participantes" in pergunta_lower:
            reformulacoes.extend([
                "reunião com discussão sobre responsáveis e equipe do projeto",
                "pessoas mencionadas na reunião sobre crédito e produtores"
            ])
        
        if "objetivo" in pergunta_lower or "meta" in pergunta_lower:
            reformulacoes.extend([
                "objetivo principal do projeto de crédito para produtores",
                "meta do programa de microcrédito e inclusão financeira"
            ])
        
        if "decisão" in pergunta_lower or "decidido" in pergunta_lower:
            reformulacoes.extend([
                "decisões tomadas sobre critérios de crédito e garantias",
                "definições aprovadas para o projeto piloto"
            ])
        
        if "problema" in pergunta_lower:
            reformulacoes.extend([
                "desafios e riscos no programa de crédito",
                "dificuldades identificadas com produtores informais"
            ])
        
        # Se não houver mapeamento específico, criar reformulação genérica
        if not reformulacoes:
            reformulacoes.append(f"informações detalhadas sobre {pergunta}")
        
        return reformulacoes
    
    def processar_pergunta(self, pergunta: str) -> str:
        """Processa uma pergunta e retorna a resposta"""
        print(f"Processando pergunta: {pergunta}")
        
        # Buscar chunks usando múltiplas estratégias
        chunks_relevantes = self.buscar_chunks_relevantes_multiplos(pergunta, num_resultados=8)
        
        # Sempre tentar gerar uma resposta, mesmo com poucos chunks
        if len(chunks_relevantes) < 2:
            # Buscar mais chunks com threshold muito baixo
            print("Poucos chunks encontrados, expandindo busca...")
            chunks_relevantes = self._buscar_chunks_recentes(5)
        
        # Preparar contexto
        contexto_reunioes = self._preparar_contexto(chunks_relevantes)
        
        # Gerar resposta com instrução para ser criativo
        resposta = self._gerar_resposta_criativa(pergunta, contexto_reunioes)
        
        return resposta
    
    def _preparar_contexto(self, chunks: List[Dict]) -> str:
        """Prepara o contexto dos chunks para o LLM"""
        if not chunks:
            return "Não há contexto específico disponível."
            
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
    
    def _gerar_resposta_criativa(self, pergunta: str, contexto: str) -> str:
        """Gera resposta sendo criativo com o contexto disponível"""
        
        prompt = f"""Com base no contexto das reuniões abaixo, responda à pergunta do usuário.

INSTRUÇÕES IMPORTANTES:
1. Se não encontrar a informação exata solicitada, extraia informações relacionadas ou relevantes
2. Sempre forneça valor, mesmo que seja um resumo geral do que foi discutido
3. Se a pergunta for sobre participantes e não houver lista explícita, mencione as pessoas citadas no contexto
4. Se a pergunta for sobre objetivos e não estiver explícito, infira dos temas discutidos
5. Seja criativo e útil, evite dizer apenas "não encontrei informação"

CONTEXTO DAS REUNIÕES:
{contexto}

PERGUNTA DO USUÁRIO:
{pergunta}

Forneça uma resposta útil e informativa baseada no contexto disponível."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Aumentar temperatura para mais criatividade
                max_tokens=600
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao processar resposta: {str(e)}"

# Atualizar a classe de integração
class IntegracaoAssistenteReunioesAprimorada:
    def __init__(self):
        self.agente = AgenteBuscaReunioesAprimorado()
    
    def processar_mensagem_usuario(self, mensagem: str) -> str:
        """Interface principal para o FRONT.py"""
        try:
            resposta = self.agente.processar_pergunta(mensagem)
            return resposta
        except Exception as e:
            # Em caso de erro, tentar fornecer algo útil
            print(f"Erro no processamento: {e}")
            return self._gerar_resposta_emergencia(mensagem)
    
    def _gerar_resposta_emergencia(self, mensagem: str) -> str:
        """Resposta de emergência quando há falha total"""
        return f"""Estou com dificuldades técnicas para acessar as informações completas das reuniões no momento.

Sobre sua pergunta: "{mensagem}"

Posso informar que temos registros de reuniões sobre o projeto de crédito para produtores informais, 
incluindo discussões sobre critérios de elegibilidade, garantias, e implementação de um projeto piloto.

Por favor, tente reformular sua pergunta ou pergunte sobre aspectos específicos como:
- Decisões tomadas sobre o projeto
- Critérios definidos para concessão de crédito
- Estrutura do projeto piloto
- Desafios identificados

Peço desculpas pelo inconveniente."""