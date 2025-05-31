"""
Agente de Brainstorm do Sistema AURALIS
Responsável por gerar ideias e propostas criativas baseadas em reuniões
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import openai
import sys
sys.path.append('../..')
from shared.config import OPENAI_API_KEY, OPENAI_MODEL
from src.database.supabase_client import supabase_client

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

class AgenteBrainstorm:
    """Gera ideias e propostas baseadas no histórico de reuniões"""
    
    def __init__(self):
        self.model = OPENAI_MODEL
        
    async def gerar_ideias(self, parametros: Dict) -> Dict:
        """
        Gera ideias criativas baseadas no contexto
        
        Args:
            parametros: Dicionário com pergunta, tópicos, contexto, etc.
            
        Returns:
            Resposta estruturada com ideias geradas
        """
        try:
            # Buscar contexto relevante
            contexto_reunioes = await self._buscar_contexto_reunioes(parametros)
            
            # Gerar ideias usando IA
            ideias = await self._gerar_ideias_ia(
                pergunta=parametros.get('pergunta'),
                topicos=parametros.get('topicos', []),
                contexto_reunioes=contexto_reunioes,
                area_usuario=parametros.get('area_usuario')
            )
            
            return {
                'sucesso': True,
                'ideias': ideias,
                'contexto_usado': len(contexto_reunioes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar ideias: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Não foi possível gerar ideias no momento.'
            }
    
    async def _buscar_contexto_reunioes(self, parametros: Dict) -> List[Dict]:
        """Busca reuniões relevantes para o contexto"""
        reunioes_relevantes = []
        
        try:
            # Buscar por palavras-chave
            if parametros.get('topicos'):
                for topico in parametros['topicos']:
                    reunioes = await supabase_client.search_meetings(topico, limit=5)
                    reunioes_relevantes.extend(reunioes)
            
            # Buscar reuniões recentes se não houver contexto específico
            if not reunioes_relevantes:
                reunioes_relevantes = await supabase_client.get_meetings(limit=10)
            
            # Remover duplicatas
            vistos = set()
            reunioes_unicas = []
            for r in reunioes_relevantes:
                if r['id'] not in vistos:
                    vistos.add(r['id'])
                    reunioes_unicas.append(r)
            
            logger.info(f"Encontradas {len(reunioes_unicas)} reuniões relevantes para brainstorm")
            return reunioes_unicas[:10]  # Limitar a 10 reuniões
            
        except Exception as e:
            logger.error(f"Erro ao buscar contexto de reuniões: {e}")
            return []
    
    async def _gerar_ideias_ia(self, pergunta: str, topicos: List[str], 
                              contexto_reunioes: List[Dict], area_usuario: str) -> List[Dict]:
        """Gera ideias usando IA"""
        
        # Preparar contexto das reuniões
        contexto_str = ""
        if contexto_reunioes:
            contexto_str = "Contexto de reuniões relevantes:\n"
            for r in contexto_reunioes[:5]:  # Limitar contexto
                contexto_str += f"\n- {r.get('titulo')} ({r.get('data_reuniao')})"
                if r.get('resumo_executivo'):
                    contexto_str += f"\n  Resumo: {r.get('resumo_executivo')[:200]}..."
                if r.get('decisoes'):
                    contexto_str += f"\n  Decisões principais: {', '.join([d.get('decisao', '') for d in r.get('decisoes', [])[:3]])}"
        
        prompt = f"""
        Como especialista em inovação e brainstorming corporativo, gere ideias criativas para:
        
        Solicitação: {pergunta}
        
        Tópicos relacionados: {', '.join(topicos) if topicos else 'Geral'}
        Área do solicitante: {area_usuario or 'Não especificada'}
        
        {contexto_str}
        
        Gere 5 ideias inovadoras e práticas. Para cada ideia, forneça:
        1. Título criativo e descritivo
        2. Descrição detalhada (2-3 parágrafos)
        3. Benefícios esperados
        4. Passos iniciais para implementação
        5. Recursos necessários
        6. Prazo estimado
        7. Nível de complexidade (Baixa/Média/Alta)
        
        Responda em JSON com a estrutura:
        {{
            "ideias": [
                {{
                    "titulo": "Título da ideia",
                    "descricao": "Descrição detalhada",
                    "beneficios": ["benefício 1", "benefício 2"],
                    "passos_iniciais": ["passo 1", "passo 2", "passo 3"],
                    "recursos": ["recurso 1", "recurso 2"],
                    "prazo_estimado": "2-3 meses",
                    "complexidade": "Média",
                    "relevancia_score": 0.95
                }}
            ],
            "insights_gerais": "Observações sobre padrões identificados e oportunidades"
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um especialista em inovação corporativa e brainstorming, conhecido por gerar ideias práticas e inovadoras que agregam valor real aos negócios."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Mais criatividade
                max_tokens=2000
            )
            
            resultado = json.loads(response.choices[0].message.content)
            
            # Processar e enriquecer ideias
            ideias_processadas = []
            for ideia in resultado.get('ideias', []):
                ideia_enriquecida = {
                    **ideia,
                    'gerada_em': datetime.now().isoformat(),
                    'baseada_em_reunioes': len(contexto_reunioes) > 0,
                    'area_origem': area_usuario
                }
                ideias_processadas.append(ideia_enriquecida)
            
            return ideias_processadas
            
        except Exception as e:
            logger.error(f"Erro ao gerar ideias com IA: {e}")
            # Retornar ideias genéricas em caso de erro
            return [{
                'titulo': 'Análise de Oportunidades',
                'descricao': 'Realizar uma análise detalhada das oportunidades identificadas nas últimas reuniões.',
                'beneficios': ['Melhor aproveitamento de oportunidades', 'Decisões mais informadas'],
                'passos_iniciais': ['Revisar atas de reuniões', 'Identificar padrões', 'Criar plano de ação'],
                'recursos': ['Equipe de análise', 'Ferramentas de BI'],
                'prazo_estimado': '1-2 meses',
                'complexidade': 'Média',
                'relevancia_score': 0.7
            }]
    
    async def refinar_ideia(self, ideia: Dict, feedback: str) -> Dict:
        """Refina uma ideia específica com base em feedback"""
        
        prompt = f"""
        Refine a seguinte ideia com base no feedback fornecido:
        
        Ideia original:
        - Título: {ideia.get('titulo')}
        - Descrição: {ideia.get('descricao')}
        - Benefícios: {', '.join(ideia.get('beneficios', []))}
        
        Feedback do usuário: {feedback}
        
        Gere uma versão refinada da ideia que:
        1. Incorpore o feedback fornecido
        2. Mantenha os pontos fortes originais
        3. Seja mais específica e acionável
        4. Considere possíveis obstáculos mencionados
        
        Responda no mesmo formato JSON da ideia original.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em refinamento de ideias e propostas corporativas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=1500
            )
            
            ideia_refinada = json.loads(response.choices[0].message.content)
            ideia_refinada['versao'] = ideia.get('versao', 1) + 1
            ideia_refinada['refinada_em'] = datetime.now().isoformat()
            ideia_refinada['feedback_aplicado'] = feedback
            
            return {
                'sucesso': True,
                'ideia_refinada': ideia_refinada
            }
            
        except Exception as e:
            logger.error(f"Erro ao refinar ideia: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Não foi possível refinar a ideia no momento.'
            }

# Instância singleton do agente de brainstorm
agente_brainstorm = AgenteBrainstorm()