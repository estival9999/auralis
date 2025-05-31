"""
Agente Orquestrador do Sistema AURALIS
Responsável por interpretar perguntas e direcionar para agentes especializados
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import openai
import sys
sys.path.append('../..')
from shared.config import OPENAI_API_KEY, OPENAI_MODEL

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

class AgenteOrquestrador:
    """Orquestra as interações entre usuário e agentes especializados"""
    
    def __init__(self):
        self.context_history: List[Dict] = []
        self.model = OPENAI_MODEL
        
    async def processar_pergunta(self, pergunta: str, contexto: Optional[Dict] = None) -> Dict:
        """
        Processa pergunta do usuário e determina qual agente deve responder
        
        Args:
            pergunta: Pergunta do usuário
            contexto: Contexto adicional (usuário, histórico, etc)
            
        Returns:
            Resposta estruturada com agente selecionado e parâmetros
        """
        try:
            # Analisar intenção da pergunta
            intencao = await self._analisar_intencao(pergunta, contexto)
            
            # Rotear para agente apropriado
            if intencao['tipo'] == 'consulta_reuniao':
                return await self._preparar_consulta_reuniao(pergunta, intencao, contexto)
            
            elif intencao['tipo'] == 'brainstorm':
                return await self._preparar_brainstorm(pergunta, intencao, contexto)
            
            elif intencao['tipo'] == 'consulta_conhecimento':
                return await self._preparar_consulta_conhecimento(pergunta, intencao, contexto)
            
            elif intencao['tipo'] == 'analise_equipe':
                return await self._preparar_analise_equipe(pergunta, intencao, contexto)
            
            else:
                # Resposta direta do orquestrador
                return await self._responder_direto(pergunta, contexto)
                
        except Exception as e:
            logger.error(f"Erro ao processar pergunta: {e}")
            
            # Importar fallback
            try:
                sys.path.append('../../src/core')
                from fallback_responses import FallbackResponses
                fallback_msg = FallbackResponses.get_simple_response(pergunta)
                return {
                    'sucesso': True,
                    'resposta': fallback_msg,
                    'tipo_resposta': 'fallback'
                }
            except:
                return {
                    'sucesso': False,
                    'erro': str(e),
                    'mensagem': 'Desculpe, ocorreu um erro ao processar sua pergunta.'
                }
    
    async def _analisar_intencao(self, pergunta: str, contexto: Optional[Dict]) -> Dict:
        """Analisa a intenção da pergunta usando IA"""
        
        prompt = f"""
        Analise a seguinte pergunta e determine a intenção do usuário:
        
        Pergunta: {pergunta}
        
        Contexto do usuário:
        - Nome: {contexto.get('usuario', {}).get('nome_completo', 'Não informado')}
        - Área: {contexto.get('usuario', {}).get('area', 'Não informada')}
        
        Classifique a pergunta em uma das seguintes categorias:
        1. consulta_reuniao - Busca informações sobre reuniões específicas
        2. brainstorm - Solicita ideias ou sugestões criativas
        3. consulta_conhecimento - Busca informações na base de conhecimento
        4. analise_equipe - Análise de dinâmica de equipe ou performance
        5. geral - Outras perguntas gerais
        
        Extraia também:
        - Palavras-chave relevantes
        - Período de tempo mencionado (se houver)
        - Pessoas mencionadas (se houver)
        - Tópicos específicos
        
        Responda em JSON com a estrutura:
        {{
            "tipo": "categoria",
            "palavras_chave": ["palavra1", "palavra2"],
            "periodo": "descrição do período ou null",
            "pessoas": ["pessoa1", "pessoa2"],
            "topicos": ["topico1", "topico2"],
            "confianca": 0.95
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um analisador de intenções especializado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            resultado = json.loads(response.choices[0].message.content)
            logger.info(f"Intenção identificada: {resultado['tipo']} (confiança: {resultado['confianca']})")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao analisar intenção: {e}")
            return {
                "tipo": "geral",
                "palavras_chave": [],
                "periodo": None,
                "pessoas": [],
                "topicos": [],
                "confianca": 0.5
            }
    
    async def _preparar_consulta_reuniao(self, pergunta: str, intencao: Dict, contexto: Dict) -> Dict:
        """Prepara consulta para o agente de reuniões"""
        return {
            'agente': 'consulta_inteligente',
            'acao': 'buscar_reunioes',
            'parametros': {
                'pergunta': pergunta,
                'palavras_chave': intencao.get('palavras_chave', []),
                'periodo': intencao.get('periodo'),
                'pessoas': intencao.get('pessoas', []),
                'contexto_usuario': contexto.get('usuario', {})
            }
        }
    
    async def _preparar_brainstorm(self, pergunta: str, intencao: Dict, contexto: Dict) -> Dict:
        """Prepara solicitação para o agente de brainstorm"""
        return {
            'agente': 'brainstorm',
            'acao': 'gerar_ideias',
            'parametros': {
                'pergunta': pergunta,
                'topicos': intencao.get('topicos', []),
                'contexto_reunioes': intencao.get('periodo'),
                'area_usuario': contexto.get('usuario', {}).get('area')
            }
        }
    
    async def _preparar_consulta_conhecimento(self, pergunta: str, intencao: Dict, contexto: Dict) -> Dict:
        """Prepara consulta para a base de conhecimento"""
        return {
            'agente': 'consulta_inteligente',
            'acao': 'buscar_conhecimento',
            'parametros': {
                'pergunta': pergunta,
                'palavras_chave': intencao.get('palavras_chave', []),
                'topicos': intencao.get('topicos', [])
            }
        }
    
    async def _preparar_analise_equipe(self, pergunta: str, intencao: Dict, contexto: Dict) -> Dict:
        """Prepara análise de equipe"""
        return {
            'agente': 'consulta_inteligente',
            'acao': 'analisar_equipe',
            'parametros': {
                'pergunta': pergunta,
                'periodo': intencao.get('periodo'),
                'pessoas': intencao.get('pessoas', []),
                'area': contexto.get('usuario', {}).get('area')
            }
        }
    
    async def _responder_direto(self, pergunta: str, contexto: Dict) -> Dict:
        """Responde diretamente perguntas gerais"""
        
        prompt = f"""
        Responda a seguinte pergunta de forma útil e concisa:
        
        Pergunta: {pergunta}
        
        Contexto:
        - Sistema: AURALIS - Sistema de Reuniões e Gestão do Conhecimento
        - Usuário: {contexto.get('usuario', {}).get('nome_completo', 'Usuário')}
        - Área: {contexto.get('usuario', {}).get('area', 'Não informada')}
        
        Seja cordial e profissional. Se não souber a resposta, sugira como o usuário pode obter a informação.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é o assistente AURALIS, especializado em gestão de reuniões e conhecimento corporativo."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            resposta = response.choices[0].message.content
            
            return {
                'sucesso': True,
                'agente': 'orquestrador',
                'resposta': resposta,
                'tipo_resposta': 'direta'
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta direta: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Desculpe, não consegui processar sua pergunta no momento.'
            }
    
    def adicionar_ao_contexto(self, mensagem: Dict):
        """Adiciona mensagem ao histórico de contexto"""
        self.context_history.append({
            'timestamp': datetime.now().isoformat(),
            'mensagem': mensagem
        })
        
        # Manter apenas as últimas 10 mensagens
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
    
    def limpar_contexto(self):
        """Limpa o histórico de contexto"""
        self.context_history = []
        logger.info("Contexto do orquestrador limpo")

# Instância singleton do orquestrador
agente_orquestrador = AgenteOrquestrador()