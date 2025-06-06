"""
Agente de IA universal para busca semântica em múltiplas fontes
- Busca em reuniões e base de conhecimento
- Prioriza informações recentes
- Melhor precisão na busca
- Considera contexto temporal
- Sistema de memória contextual integrado
- Unifica resultados de diferentes fontes
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

# Importar sistema de memória
try:
    from .memoria_contextual import obter_gerenciador_memoria
except ImportError:
    from memoria_contextual import obter_gerenciador_memoria

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
        
        # Sistema de memória contextual
        self.gerenciador_memoria = obter_gerenciador_memoria()
        
        # Prompt sistema aprimorado
        self.system_prompt = """Você é um assistente inteligente com acesso a múltiplas fontes de conhecimento corporativo.

REGRAS CRÍTICAS DE COMUNICAÇÃO:
1. Para pedidos de ajuda vagos: responda com UMA pergunta curta e direta
2. Seja CONCISO - evite antecipar soluções sem conhecer o problema
3. Use linguagem natural e conversacional
4. Para saudações simples: responda brevemente e ofereça ajuda
5. NUNCA invente informações - use apenas o contexto fornecido
6. Se a informação não estiver disponível:
   - Para perguntas específicas: explique brevemente e sugira alternativas
   - Para pedidos vagos: apenas pergunte qual é o problema
7. SEMPRE cite as fontes quando fornecer informações específicas
8. Evite respostas longas a menos que seja absolutamente necessário

IMPORTANTE: Seja natural e direto. Não "fale demais" antes de entender a necessidade real do usuário.

Suas capacidades:
- Buscar informações em reuniões gravadas
- Consultar base de conhecimento
- Responder sobre políticas e procedimentos
- Fornecer informações de documentos oficiais"""

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
    
    def _buscar_em_reunioes(self, pergunta: str) -> List[Dict]:
        """Busca chunks relevantes nas reuniões"""
        try:
            # Buscar todos os embeddings de reuniões
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
                    chunk['fonte'] = 'reuniao'
                    resultados_com_score.append(chunk)
                    
                except Exception as e:
                    print(f"Erro ao processar chunk de reunião {chunk.get('id')}: {e}")
                    continue
            
            return resultados_com_score
            
        except Exception as e:
            print(f"Erro ao buscar em reuniões: {e}")
            return []
    
    def _buscar_em_base_conhecimento(self, pergunta: str) -> List[Dict]:
        """Busca chunks relevantes na base de conhecimento"""
        try:
            # Normalizar pergunta para melhor busca
            pergunta_normalizada = pergunta.replace('"', '').replace("'", "")
            
            # Gerar embedding da pergunta
            embedding_pergunta = self.gerar_embedding_pergunta(pergunta_normalizada)
            
            # Usar função RPC do Supabase para busca
            resultado = self.supabase.rpc('buscar_conhecimento_similar', {
                'query_embedding': embedding_pergunta,
                'limite': 15  # Aumentar limite para capturar mais resultados
            }).execute()
            
            if not resultado.data:
                return []
            
            # Formatar resultados para compatibilidade
            resultados_formatados = []
            for item in resultado.data:
                chunk_formatado = {
                    'id': item.get('id'),
                    'chunk_texto': item.get('conteudo'),
                    'arquivo_origem': item.get('documento_origem'),
                    'titulo': item.get('tipo_documento', '').title(),
                    'responsavel': 'Sistema',
                    'data_reuniao': 'N/A',
                    'similarity': item.get('similaridade', 0),
                    'fonte': 'documento',
                    'tipo_documento': item.get('tipo_documento'),
                    'categoria': item.get('categoria'),
                    'tags': item.get('tags', [])
                }
                resultados_formatados.append(chunk_formatado)
            
            return resultados_formatados
            
        except Exception as e:
            print(f"Erro ao buscar na base de conhecimento: {e}")
            # Fallback: busca direta se RPC não existir
            try:
                return self._buscar_base_conhecimento_direto(pergunta)
            except:
                return []
    
    def _buscar_base_conhecimento_direto(self, pergunta: str) -> List[Dict]:
        """Busca direta na base de conhecimento (fallback)"""
        try:
            # Buscar todos os registros
            resultado = self.supabase.table('base_conhecimento').select('*').eq('ativo', True).execute()
            
            if not resultado.data:
                return []
            
            # Gerar embedding da pergunta
            embedding_pergunta = self.gerar_embedding_pergunta(pergunta)
            
            resultados_com_score = []
            for doc in resultado.data:
                try:
                    # Obter embedding
                    embedding_doc = doc.get('embedding', [])
                    
                    # Se for string JSON, converter
                    if isinstance(embedding_doc, str):
                        embedding_doc = json.loads(embedding_doc)
                    
                    # Verificar dimensões
                    if not embedding_doc or len(embedding_doc) != 1536:
                        continue
                    
                    # Calcular similaridade
                    similaridade = self.calcular_similaridade_com_peso_temporal(
                        embedding_pergunta,
                        embedding_doc,
                        doc.get('data_processamento')
                    )
                    
                    # Formatar resultado
                    chunk_formatado = {
                        'id': doc.get('id'),
                        'chunk_texto': doc.get('conteudo'),
                        'arquivo_origem': doc.get('documento_origem'),
                        'titulo': doc.get('tipo_documento', '').title(),
                        'responsavel': 'Sistema',
                        'data_reuniao': 'N/A',
                        'similarity': similaridade,
                        'fonte': 'documento',
                        'tipo_documento': doc.get('tipo_documento'),
                        'categoria': doc.get('categoria'),
                        'tags': doc.get('tags', [])
                    }
                    resultados_com_score.append(chunk_formatado)
                    
                except Exception as e:
                    print(f"Erro ao processar documento {doc.get('id')}: {e}")
                    continue
            
            return resultados_com_score
            
        except Exception as e:
            print(f"Erro na busca direta: {e}")
            return []
    
    def _diversificar_resultados(self, resultados: List[Dict], num_resultados: int) -> List[Dict]:
        """Diversifica resultados para incluir diferentes fontes"""
        resultados_finais = []
        reunioes_incluidas = 0
        documentos_incluidos = 0
        max_por_fonte = num_resultados // 2 + 1
        
        for resultado in resultados:
            fonte = resultado.get('fonte', 'reuniao')
            
            # Limitar por fonte para garantir diversidade
            if fonte == 'reuniao' and reunioes_incluidas < max_por_fonte:
                resultados_finais.append(resultado)
                reunioes_incluidas += 1
            elif fonte == 'documento' and documentos_incluidos < max_por_fonte:
                resultados_finais.append(resultado)
                documentos_incluidos += 1
            
            if len(resultados_finais) >= num_resultados:
                break
        
        return resultados_finais
    
    def gerar_embedding_pergunta(self, pergunta: str) -> List[float]:
        """Gera embedding para a pergunta do usuário"""
        try:
            # Normalizar pergunta removendo aspas e variações
            pergunta_normalizada = pergunta.replace('"', '').replace("'", "")
            
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=pergunta_normalizada
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro ao gerar embedding da pergunta: {e}")
            raise
    
    def buscar_chunks_relevantes(self, pergunta: str, num_resultados: int = 5) -> List[Dict]:
        """Busca chunks relevantes em reuniões e base de conhecimento"""
        try:
            # Detectar contexto temporal
            contexto_temporal = self.detectar_busca_temporal(pergunta)
            
            # Se busca a última reunião, retornar diretamente
            if contexto_temporal['busca_recente'] and 'reunião' in pergunta.lower():
                reuniao_recente = self.buscar_reuniao_mais_recente()
                if reuniao_recente:
                    return [{
                        **reuniao_recente,
                        'similarity': 1.0,  # Alta relevância para busca direta
                        'fonte': 'reuniao'
                    }]
            
            # Buscar em ambas as fontes
            resultados_reunioes = self._buscar_em_reunioes(pergunta)
            resultados_conhecimento = self._buscar_em_base_conhecimento(pergunta)
            
            # Combinar resultados
            todos_resultados = resultados_reunioes + resultados_conhecimento
            
            # Se não encontrou resultados muito relevantes, tentar busca com termos individuais
            if not todos_resultados or (todos_resultados and max(r['similarity'] for r in todos_resultados) < 0.7):
                # Quebrar pergunta em termos
                termos = pergunta.replace('"', '').replace("'", "").split()
                for termo in termos:
                    if len(termo) > 3:  # Ignorar termos muito curtos
                        mais_resultados = self._buscar_em_base_conhecimento(termo)
                        todos_resultados.extend(mais_resultados)
            
            # Remover duplicatas mantendo maior similaridade
            resultados_unicos = {}
            for r in todos_resultados:
                chave = r.get('id', r.get('arquivo_origem', ''))
                if chave not in resultados_unicos or r['similarity'] > resultados_unicos[chave]['similarity']:
                    resultados_unicos[chave] = r
            
            todos_resultados = list(resultados_unicos.values())
            
            # Ordenar todos os resultados por similaridade
            todos_resultados.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Retornar top N com diversidade de fontes
            return self._diversificar_resultados(todos_resultados, num_resultados)
            
        except Exception as e:
            print(f"Erro ao buscar chunks: {e}")
            return []
    
    def _e_pergunta_ambigua(self, pergunta: str) -> bool:
        """Detecta perguntas muito vagas ou ambíguas"""
        termos_ambiguos = [
            'isso', 'aquilo', 'ele', 'ela', 'eles',
            'o que aconteceu', 'me explique', 'como assim',
            'o que foi', 'qual foi', 'me fale sobre'
        ]
        
        pergunta_limpa = pergunta.lower().strip()
        
        # Se muito curta E contém termo ambíguo
        if len(pergunta_limpa.split()) <= 4:
            for termo in termos_ambiguos:
                if termo in pergunta_limpa:
                    return True
        return False
    
    def _e_pergunta_generica(self, pergunta: str) -> bool:
        """Detecta perguntas conceituais/genéricas"""
        termos_genericos = [
            'como melhorar', 'o que é', 'qual a importância',
            'melhores práticas', 'dicas para', 'estratégias de',
            'o que você acha', 'sua opinião sobre'
        ]
        
        pergunta_lower = pergunta.lower()
        for termo in termos_genericos:
            if termo in pergunta_lower:
                return True
        return False
    
    def _e_pergunta_sobre_reuniao_especifica(self, pergunta: str) -> tuple[bool, str]:
        """Detecta perguntas genéricas sobre reuniões específicas"""
        import re
        
        pergunta_lower = pergunta.lower()
        
        # Padrões comuns
        padroes_reuniao = [
            r'me (?:fale|conte|diga) sobre a reuni[ãa]o (?:de |do |da )?(.+)',
            r'o que (?:teve|houve|aconteceu) na reuni[ãa]o (?:de |do |da )?(.+)',
            r'(?:sobre|qual foi) a reuni[ãa]o (?:de |do |da )?(.+)',
        ]
        
        # Se já pede algo específico, não precisa contexto
        if any(termo in pergunta_lower for termo in ['resumo', 'decisões', 'participantes']):
            return False, ""
        
        for padrao in padroes_reuniao:
            match = re.search(padrao, pergunta_lower)
            if match and match.groups():
                return True, match.group(1).strip()
        
        return False, ""
    
    def _gerar_opcoes_contexto_reuniao(self, nome_reuniao: str = "") -> str:
        """Gera menu de opções para reunião"""
        return f"""Certo, sobre a reunião{f' "{nome_reuniao}"' if nome_reuniao else ''}. 
O que você gostaria de saber?

• **Resumo geral** - Principais pontos em formato executivo
• **Discussões detalhadas** - Todos os tópicos abordados
• **Decisões e ações** - O que foi definido
• **Participantes** - Quem estava presente
• **Próximos passos** - Tarefas e responsáveis

Especifique sua necessidade para uma resposta mais precisa."""
    
    def _e_pedido_ajuda_vago(self, pergunta: str) -> bool:
        """Detecta pedidos de ajuda genéricos sem especificar o problema"""
        pergunta_lower = pergunta.lower()
        
        # Padrões de pedido de ajuda vago
        padroes_vagos = [
            r'(?:pode|poderia|consegue) me ajudar',
            r'(?:to|tô|estou) com (?:um |)problema',
            r'preciso de (?:ajuda|auxílio|socorro)',
            r'(?:tem|teria) como (?:me |)ajudar',
            r'(?:ajuda|socorro|help)(?:\s|$)',
            r'(?:não sei|nao sei) o que fazer',
            r'(?:tá|está) difícil'
        ]
        
        # Verifica se é pedido vago (sem detalhes específicos)
        import re
        for padrao in padroes_vagos:
            if re.search(padrao, pergunta_lower):
                # Verifica se a mensagem tem menos de 10 palavras (muito curta)
                if len(pergunta.split()) < 10:
                    return True
        
        return False
    
    def _gerar_resposta_ajuda_concisa(self) -> str:
        """Gera resposta concisa para pedidos de ajuda vagos"""
        respostas_possiveis = [
            "Claro! Qual problema você está enfrentando?",
            "Claro! Como posso ajudar?",
            "Sim! Me conte o que está acontecendo.",
            "Claro! O que você precisa?",
            "Com certeza! Qual é a dificuldade?"
        ]
        
        # Escolher aleatoriamente para variar
        import random
        return random.choice(respostas_possiveis)
    
    def processar_pergunta(self, pergunta: str) -> str:
        """Processa uma pergunta e retorna a resposta"""
        print(f"Processando pergunta: {pergunta}")
        
        # Detectar saudações simples
        saudacoes = ['olá', 'ola', 'oi', 'bom dia', 'boa tarde', 'boa noite']
        pergunta_lower = pergunta.lower().strip()
        
        if pergunta_lower in saudacoes:
            resposta = "Olá! Como posso ajudá-lo com informações sobre as reuniões?"
            # Registrar na memória
            self.gerenciador_memoria.processar_interacao(pergunta, resposta)
            return resposta
        
        # NOVO: Verificar pedidos de ajuda vagos ANTES de outras verificações
        if self._e_pedido_ajuda_vago(pergunta):
            resposta = self._gerar_resposta_ajuda_concisa()
            self.gerenciador_memoria.processar_interacao(pergunta, resposta)
            return resposta
        
        # NOVO: Verificar ambiguidade primeiro
        if self._e_pergunta_ambigua(pergunta):
            # Verificar se há contexto anterior na memória
            contexto_anterior = self.gerenciador_memoria.obter_contexto()
            
            if not contexto_anterior or len(contexto_anterior) < 50:
                resposta = "Sua pergunta está um pouco vaga. Você poderia fornecer mais detalhes? Por exemplo:\n"
                resposta += "- Sobre qual reunião específica você quer saber?\n"
                resposta += "- Qual assunto ou tema você está procurando?\n"
                resposta += "- Em que período isso ocorreu?"
                
                self.gerenciador_memoria.processar_interacao(pergunta, resposta)
                return resposta
        
        # NOVO: Verificar se é pergunta sobre reunião específica mas genérica
        e_sobre_reuniao, nome_reuniao = self._e_pergunta_sobre_reuniao_especifica(pergunta)
        if e_sobre_reuniao:
            # Fazer busca rápida para confirmar que a reunião existe
            chunks_teste = self.buscar_chunks_relevantes(pergunta, num_resultados=1)
            
            if chunks_teste:
                # Reunião encontrada - solicitar contexto
                resposta = self._gerar_opcoes_contexto_reuniao(nome_reuniao)
                self.gerenciador_memoria.processar_interacao(pergunta, resposta)
                return resposta
        
        # Verificar se é pergunta genérica e ajustar número de chunks
        if self._e_pergunta_generica(pergunta):
            # Buscar apenas 2-3 chunks para contexto opcional
            chunks_relevantes = self.buscar_chunks_relevantes(pergunta, num_resultados=2)
        else:
            # Busca normal com 5 chunks
            chunks_relevantes = self.buscar_chunks_relevantes(pergunta, num_resultados=5)
        
        if not chunks_relevantes:
            # Tentar entender o que foi perguntado e sugerir alternativas
            resposta = f"Não encontrei informações específicas sobre '{pergunta}' nas reuniões gravadas ou documentos disponíveis. "
            resposta += "Posso ajudá-lo com outras informações sobre reuniões, procedimentos operacionais, políticas da cooperativa ou linhas de crédito. "
            resposta += "Você poderia reformular sua pergunta ou especificar melhor o que procura?"
            # Registrar na memória
            self.gerenciador_memoria.processar_interacao(pergunta, resposta)
            return resposta
        
        # Preparar contexto
        contexto = self._preparar_contexto(chunks_relevantes)
        
        # Obter contexto da memória
        contexto_memoria = self.gerenciador_memoria.obter_contexto()
        
        # Gerar resposta com contexto completo
        resposta = self._gerar_resposta(pergunta, contexto, contexto_memoria)
        
        # Extrair reuniões mencionadas
        reunioes_mencionadas = list(set([chunk.get('arquivo_origem', '') for chunk in chunks_relevantes[:3]]))
        
        # Registrar na memória
        self.gerenciador_memoria.processar_interacao(
            pergunta, 
            resposta,
            reunioes_encontradas=reunioes_mencionadas,
            confidence_score=chunks_relevantes[0].get('similarity', 0) if chunks_relevantes else 0
        )
        
        return resposta
    
    def _preparar_contexto(self, chunks: List[Dict]) -> str:
        """Prepara o contexto dos chunks para o LLM"""
        contexto = ""
        items_vistos = set()
        
        for i, chunk in enumerate(chunks):
            fonte = chunk.get('fonte', 'reuniao')
            
            if fonte == 'reuniao':
                # Extrair informações de reunião
                arquivo = chunk.get('arquivo_origem', 'Arquivo desconhecido')
                titulo = chunk.get('titulo', chunk.get('metadados', {}).get('titulo', 'Sem título'))
                data = chunk.get('data_reuniao', 'Data não informada')
                hora = chunk.get('hora_inicio', '')
                responsavel = chunk.get('responsavel', '')
                texto = chunk.get('chunk_texto', '')
                similaridade = chunk.get('similarity', 0)
                
                # Identificador único da reunião
                item_id = f"{arquivo}_{data}"
                
                # Adicionar cabeçalho da reunião se for nova
                if item_id not in items_vistos:
                    contexto += f"\n\n=== REUNIÃO {i+1}: {titulo} ==="
                    contexto += f"\nData: {data}"
                    if hora:
                        contexto += f" às {hora}"
                    if responsavel:
                        contexto += f"\nResponsável: {responsavel}"
                    contexto += f"\nRelevância: {similaridade:.2%}\n"
                    items_vistos.add(item_id)
                
                # Adicionar texto do chunk
                contexto += f"\n{texto}\n"
                
            else:  # fonte == 'documento'
                # Extrair informações do documento
                arquivo = chunk.get('arquivo_origem', 'Documento desconhecido')
                tipo = chunk.get('tipo_documento', 'documento').upper()
                categoria = chunk.get('categoria', '')
                tags = chunk.get('tags', [])
                texto = chunk.get('chunk_texto', '')
                similaridade = chunk.get('similarity', 0)
                
                # Identificador único do documento
                item_id = f"doc_{arquivo}"
                
                # Adicionar cabeçalho do documento se for novo
                if item_id not in items_vistos:
                    contexto += f"\n\n=== DOCUMENTO {i+1}: {tipo} - {arquivo} ==="
                    if categoria:
                        contexto += f"\nCategoria: {categoria}"
                    if tags:
                        contexto += f"\nTags: {', '.join(tags)}"
                    contexto += f"\nRelevância: {similaridade:.2%}\n"
                    items_vistos.add(item_id)
                
                # Adicionar texto do chunk
                contexto += f"\n{texto}\n"
        
        return contexto
    
    def _gerar_resposta(self, pergunta: str, contexto: str, contexto_memoria: str = "") -> str:
        """Gera resposta usando o contexto encontrado e histórico da conversa"""
        
        # Detectar se é pergunta sobre última reunião
        contexto_temporal = self.detectar_busca_temporal(pergunta)
        
        instrucoes_extras = ""
        if contexto_temporal['busca_recente']:
            instrucoes_extras = "\nIMPORTANTE: A primeira reunião no contexto é a MAIS RECENTE. Responda baseando-se nela."
        
        # Incluir contexto da memória se disponível
        contexto_completo = ""
        if contexto_memoria:
            contexto_completo = f"{contexto_memoria}\n\n"
        
        # Detectar se é pergunta genérica para ajustar o prompt
        e_generica = self._e_pergunta_generica(pergunta)
        
        if e_generica:
            prompt = f"""Responda a pergunta seguindo estas diretrizes:

DIRETRIZES IMPORTANTES:
1. PRIMEIRO avalie se a pergunta é genérica/conceitual ou específica sobre dados
2. Para perguntas GENÉRICAS: forneça orientações gerais úteis, mencionando dados específicos APENAS se forem muito relevantes
3. Para perguntas ESPECÍFICAS: use o contexto fornecido e cite as fontes
4. Seja natural - nem toda resposta precisa forçar uma conexão com os dados disponíveis
{instrucoes_extras}

{contexto_completo}CONTEXTO DISPONÍVEL (use apenas se relevante):
{contexto}

PERGUNTA: {pergunta}

Resposta:"""
        else:
            prompt = f"""Com base no contexto fornecido, responda a pergunta seguindo estas diretrizes:

DIRETRIZES IMPORTANTES:
1. Se encontrar a informação: forneça uma resposta completa citando SEMPRE a fonte (documento/reunião, data)
2. Se NÃO encontrar: reconheça o que foi perguntado, explique que não encontrou e sugira informações relacionadas se houver
3. Correlacione dados de múltiplas fontes quando relevante
4. Identifique possíveis desafios, riscos ou considerações importantes
5. Se não tiver certeza da intenção, peça esclarecimentos educadamente
{instrucoes_extras}

{contexto_completo}CONTEXTO (REUNIÕES E DOCUMENTOS):
{contexto}

PERGUNTA: {pergunta}

Resposta (incluindo fonte, correlações e considerações relevantes):"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Aumentar ligeiramente para respostas mais naturais
                max_tokens=800  # Aumentado para evitar truncamento de respostas
            )
            
            resposta = response.choices[0].message.content
            
            # Verificar se a resposta parece truncada
            if resposta and resposta[-1] not in '.!?"':
                resposta += "..."
            
            return resposta
        except Exception as e:
            return f"Erro ao processar resposta: {str(e)}"