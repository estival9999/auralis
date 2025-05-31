"""
Agente de Consulta Inteligente do Sistema AURALIS
Responsável por buscar e analisar informações em reuniões e base de conhecimento
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import openai
from difflib import SequenceMatcher
import sys
sys.path.append('../..')
from shared.config import OPENAI_API_KEY, OPENAI_MODEL
from src.database.supabase_client import supabase_client

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

class AgenteConsultaInteligente:
    """Realiza buscas inteligentes e análises no histórico"""
    
    def __init__(self):
        self.model = OPENAI_MODEL
        # Mapeamento de nomes comuns (correção de transcrição)
        self.correcoes_nomes = {
            'mateus estivau': 'Matheus Estival',
            'mateus estival': 'Matheus Estival',
            'joao silva': 'João Silva',
            'maria santos': 'Maria Santos',
            'pedro costa': 'Pedro Costa'
        }
    
    async def buscar_reunioes(self, parametros: Dict) -> Dict:
        """Busca reuniões relevantes com análise inteligente"""
        try:
            # Extrair e processar parâmetros
            pergunta = parametros.get('pergunta', '')
            palavras_chave = parametros.get('palavras_chave', [])
            periodo = parametros.get('periodo')
            pessoas = self._corrigir_nomes(parametros.get('pessoas', []))
            
            # Buscar reuniões
            reunioes = await self._buscar_reunioes_relevantes(
                palavras_chave, periodo, pessoas
            )
            
            if not reunioes:
                return {
                    'sucesso': True,
                    'reunioes': [],
                    'mensagem': 'Nenhuma reunião encontrada com os critérios especificados.',
                    'analise': None
                }
            
            # Analisar reuniões encontradas
            analise = await self._analisar_reunioes(reunioes, pergunta)
            
            return {
                'sucesso': True,
                'reunioes': reunioes,
                'total_encontrado': len(reunioes),
                'analise': analise,
                'periodo_analisado': self._formatar_periodo(reunioes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar reuniões: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Erro ao buscar reuniões.'
            }
    
    async def buscar_conhecimento(self, parametros: Dict) -> Dict:
        """Busca na base de conhecimento"""
        try:
            pergunta = parametros.get('pergunta', '')
            palavras_chave = parametros.get('palavras_chave', [])
            topicos = parametros.get('topicos', [])
            
            # Combinar termos de busca
            termos_busca = list(set(palavras_chave + topicos))
            
            # Buscar documentos relevantes
            documentos = []
            for termo in termos_busca:
                docs = await supabase_client.search_knowledge_base(termo, limit=5)
                documentos.extend(docs)
            
            # Remover duplicatas
            documentos_unicos = self._remover_duplicatas(documentos)
            
            if not documentos_unicos:
                return {
                    'sucesso': True,
                    'documentos': [],
                    'mensagem': 'Nenhum documento encontrado na base de conhecimento.',
                    'resposta': None
                }
            
            # Gerar resposta baseada nos documentos
            resposta = await self._gerar_resposta_conhecimento(
                pergunta, documentos_unicos
            )
            
            return {
                'sucesso': True,
                'documentos': documentos_unicos[:5],  # Limitar retorno
                'total_encontrado': len(documentos_unicos),
                'resposta': resposta,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Erro ao buscar na base de conhecimento.'
            }
    
    async def analisar_equipe(self, parametros: Dict) -> Dict:
        """Analisa dinâmica e performance da equipe"""
        try:
            periodo = parametros.get('periodo')
            pessoas = self._corrigir_nomes(parametros.get('pessoas', []))
            area = parametros.get('area')
            
            # Buscar reuniões do período/área
            reunioes = await self._buscar_reunioes_equipe(periodo, area, pessoas)
            
            if not reunioes:
                return {
                    'sucesso': True,
                    'analise': None,
                    'mensagem': 'Nenhuma reunião encontrada para análise de equipe.'
                }
            
            # Analisar dinâmica da equipe
            analise = await self._analisar_dinamica_equipe(reunioes, pessoas)
            
            return {
                'sucesso': True,
                'analise': analise,
                'reunioes_analisadas': len(reunioes),
                'periodo': self._formatar_periodo(reunioes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar equipe: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Erro ao analisar dinâmica da equipe.'
            }
    
    def _corrigir_nomes(self, nomes: List[str]) -> List[str]:
        """Corrige nomes com base em padrões conhecidos"""
        nomes_corrigidos = []
        
        for nome in nomes:
            nome_lower = nome.lower().strip()
            
            # Verificar correções diretas
            if nome_lower in self.correcoes_nomes:
                nomes_corrigidos.append(self.correcoes_nomes[nome_lower])
            else:
                # Buscar similaridade
                melhor_match = None
                melhor_score = 0
                
                for erro, correto in self.correcoes_nomes.items():
                    score = SequenceMatcher(None, nome_lower, erro).ratio()
                    if score > melhor_score and score > 0.8:
                        melhor_score = score
                        melhor_match = correto
                
                if melhor_match:
                    nomes_corrigidos.append(melhor_match)
                    logger.info(f"Nome corrigido: '{nome}' -> '{melhor_match}'")
                else:
                    nomes_corrigidos.append(nome)
        
        return nomes_corrigidos
    
    async def _buscar_reunioes_relevantes(self, palavras_chave: List[str], 
                                         periodo: str, pessoas: List[str]) -> List[Dict]:
        """Busca reuniões com critérios múltiplos"""
        reunioes_relevantes = []
        
        try:
            # Buscar por palavras-chave
            if palavras_chave:
                for palavra in palavras_chave:
                    reunioes = await supabase_client.search_meetings(palavra, limit=10)
                    reunioes_relevantes.extend(reunioes)
            
            # Se não houver palavras-chave, buscar recentes
            if not reunioes_relevantes:
                reunioes_relevantes = await supabase_client.get_meetings(limit=20)
            
            # Filtrar por período
            if periodo:
                reunioes_relevantes = self._filtrar_por_periodo(reunioes_relevantes, periodo)
            
            # Filtrar por pessoas
            if pessoas:
                reunioes_relevantes = self._filtrar_por_pessoas(reunioes_relevantes, pessoas)
            
            # Remover duplicatas e ordenar
            reunioes_unicas = self._remover_duplicatas(reunioes_relevantes)
            reunioes_unicas.sort(key=lambda x: x.get('data_reuniao', ''), reverse=True)
            
            return reunioes_unicas[:15]  # Limitar a 15 reuniões
            
        except Exception as e:
            logger.error(f"Erro ao buscar reuniões relevantes: {e}")
            return []
    
    def _filtrar_por_periodo(self, reunioes: List[Dict], periodo: str) -> List[Dict]:
        """Filtra reuniões por período"""
        hoje = datetime.now()
        reunioes_filtradas = []
        
        # Interpretar período
        if 'semana' in periodo.lower():
            inicio = hoje - timedelta(days=7)
        elif 'mês' in periodo.lower() or 'mes' in periodo.lower():
            inicio = hoje - timedelta(days=30)
        elif 'trimestre' in periodo.lower():
            inicio = hoje - timedelta(days=90)
        elif 'ano' in periodo.lower():
            inicio = hoje - timedelta(days=365)
        else:
            # Tentar extrair datas específicas
            return reunioes
        
        for reuniao in reunioes:
            try:
                data_reuniao = datetime.fromisoformat(reuniao.get('data_reuniao', '').replace('Z', '+00:00'))
                if data_reuniao >= inicio:
                    reunioes_filtradas.append(reuniao)
            except:
                continue
        
        return reunioes_filtradas
    
    def _filtrar_por_pessoas(self, reunioes: List[Dict], pessoas: List[str]) -> List[Dict]:
        """Filtra reuniões por pessoas mencionadas"""
        reunioes_filtradas = []
        
        for reuniao in reunioes:
            # Verificar responsável
            responsavel = reuniao.get('responsavel', '').lower()
            participantes = [p.lower() for p in reuniao.get('participantes', [])]
            transcricao = reuniao.get('transcricao_completa', '').lower()
            
            for pessoa in pessoas:
                pessoa_lower = pessoa.lower()
                if (pessoa_lower in responsavel or 
                    any(pessoa_lower in p for p in participantes) or
                    pessoa_lower in transcricao):
                    reunioes_filtradas.append(reuniao)
                    break
        
        return reunioes_filtradas
    
    def _remover_duplicatas(self, items: List[Dict]) -> List[Dict]:
        """Remove itens duplicados baseado no ID"""
        vistos = set()
        unicos = []
        
        for item in items:
            item_id = item.get('id')
            if item_id and item_id not in vistos:
                vistos.add(item_id)
                unicos.append(item)
        
        return unicos
    
    def _formatar_periodo(self, reunioes: List[Dict]) -> str:
        """Formata período coberto pelas reuniões"""
        if not reunioes:
            return "Nenhum período"
        
        datas = []
        for r in reunioes:
            try:
                data = datetime.fromisoformat(r.get('data_reuniao', '').replace('Z', '+00:00'))
                datas.append(data)
            except:
                continue
        
        if not datas:
            return "Período indefinido"
        
        data_inicio = min(datas)
        data_fim = max(datas)
        
        return f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    
    async def _analisar_reunioes(self, reunioes: List[Dict], pergunta: str) -> Dict:
        """Analisa reuniões e extrai insights"""
        
        # Preparar contexto das reuniões
        contexto = self._preparar_contexto_reunioes(reunioes[:10])  # Limitar contexto
        
        prompt = f"""
        Analise as seguintes reuniões para responder: {pergunta}
        
        {contexto}
        
        Forneça:
        1. Resposta direta à pergunta
        2. Principais decisões relacionadas
        3. Ações em andamento
        4. Tendências identificadas
        5. Recomendações
        
        Seja específico e cite reuniões quando relevante.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um analista especializado em extrair insights de reuniões corporativas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            analise_texto = response.choices[0].message.content
            
            # Estruturar análise
            return {
                'resposta_completa': analise_texto,
                'reunioes_analisadas': len(reunioes),
                'insights_extraidos': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar reuniões: {e}")
            return {
                'resposta_completa': 'Não foi possível analisar as reuniões no momento.',
                'reunioes_analisadas': len(reunioes),
                'insights_extraidos': False
            }
    
    def _preparar_contexto_reunioes(self, reunioes: List[Dict]) -> str:
        """Prepara contexto formatado das reuniões"""
        contexto = "CONTEXTO DAS REUNIÕES:\n\n"
        
        for i, reuniao in enumerate(reunioes, 1):
            contexto += f"Reunião {i}:\n"
            contexto += f"- Título: {reuniao.get('titulo')}\n"
            contexto += f"- Data: {reuniao.get('data_reuniao')}\n"
            contexto += f"- Responsável: {reuniao.get('responsavel')}\n"
            
            if reuniao.get('resumo_executivo'):
                contexto += f"- Resumo: {reuniao.get('resumo_executivo')[:300]}...\n"
            
            if reuniao.get('decisoes'):
                contexto += "- Decisões principais:\n"
                for d in reuniao.get('decisoes', [])[:3]:
                    contexto += f"  • {d.get('decisao', 'N/A')}\n"
            
            if reuniao.get('acoes'):
                contexto += "- Ações definidas:\n"
                for a in reuniao.get('acoes', [])[:3]:
                    contexto += f"  • {a.get('acao', 'N/A')} - {a.get('responsavel', 'N/A')}\n"
            
            contexto += "\n"
        
        return contexto
    
    async def _gerar_resposta_conhecimento(self, pergunta: str, documentos: List[Dict]) -> str:
        """Gera resposta baseada em documentos da base de conhecimento"""
        
        # Preparar contexto dos documentos
        contexto = "DOCUMENTOS RELEVANTES:\n\n"
        for i, doc in enumerate(documentos[:5], 1):
            contexto += f"Documento {i}: {doc.get('titulo_arquivo')}\n"
            conteudo = doc.get('conteudo', '')[:500]
            contexto += f"{conteudo}...\n\n"
        
        prompt = f"""
        Com base nos documentos fornecidos, responda: {pergunta}
        
        {contexto}
        
        Forneça uma resposta clara e completa, citando os documentos quando relevante.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente que responde perguntas com base em documentos corporativos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return "Não foi possível gerar uma resposta baseada nos documentos encontrados."
    
    async def _buscar_reunioes_equipe(self, periodo: str, area: str, pessoas: List[str]) -> List[Dict]:
        """Busca reuniões específicas da equipe"""
        reunioes = await supabase_client.get_meetings(limit=50)
        
        # Filtrar por área se especificada
        if area:
            reunioes = [r for r in reunioes if r.get('area', '').lower() == area.lower()]
        
        # Aplicar outros filtros
        if periodo:
            reunioes = self._filtrar_por_periodo(reunioes, periodo)
        
        if pessoas:
            reunioes = self._filtrar_por_pessoas(reunioes, pessoas)
        
        return reunioes
    
    async def _analisar_dinamica_equipe(self, reunioes: List[Dict], pessoas: List[str]) -> Dict:
        """Analisa dinâmica e padrões da equipe"""
        
        # Coletar estatísticas
        stats = {
            'total_reunioes': len(reunioes),
            'participacao_por_pessoa': {},
            'decisoes_totais': 0,
            'acoes_totais': 0,
            'pendencias_totais': 0
        }
        
        for reuniao in reunioes:
            # Contar decisões, ações e pendências
            stats['decisoes_totais'] += len(reuniao.get('decisoes', []))
            stats['acoes_totais'] += len(reuniao.get('acoes', []))
            stats['pendencias_totais'] += len(reuniao.get('pendencias', []))
            
            # Analisar participação
            responsavel = reuniao.get('responsavel', '')
            if responsavel:
                stats['participacao_por_pessoa'][responsavel] = stats['participacao_por_pessoa'].get(responsavel, 0) + 1
        
        # Gerar análise com IA
        contexto = self._preparar_contexto_reunioes(reunioes[:10])
        
        prompt = f"""
        Analise a dinâmica da equipe com base nas reuniões:
        
        {contexto}
        
        Estatísticas:
        - Total de reuniões: {stats['total_reunioes']}
        - Decisões tomadas: {stats['decisoes_totais']}
        - Ações definidas: {stats['acoes_totais']}
        - Pendências: {stats['pendencias_totais']}
        
        Forneça:
        1. Análise da produtividade da equipe
        2. Padrões de colaboração identificados
        3. Pontos fortes da equipe
        4. Áreas de melhoria
        5. Recomendações específicas
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de dinâmica de equipes corporativas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            return {
                'analise_completa': response.choices[0].message.content,
                'estatisticas': stats,
                'periodo_analisado': self._formatar_periodo(reunioes)
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar dinâmica da equipe: {e}")
            return {
                'analise_completa': 'Não foi possível gerar análise da equipe.',
                'estatisticas': stats,
                'periodo_analisado': self._formatar_periodo(reunioes)
            }

# Instância singleton do agente de consulta
agente_consulta_inteligente = AgenteConsultaInteligente()