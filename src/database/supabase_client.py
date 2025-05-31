"""
Cliente Supabase com suporte a MCP
Integração com banco de dados via Model Context Protocol
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from loguru import logger
import sys
sys.path.append('../..')
from shared.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

class SupabaseClient:
    """Cliente para interações com Supabase"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.initialize_client()
    
    def initialize_client(self):
        """Inicializa cliente Supabase"""
        try:
            if SUPABASE_URL and SUPABASE_SERVICE_KEY:
                # Usar service key para operações administrativas
                self.client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
                logger.info("Cliente Supabase inicializado com sucesso (service role)")
            elif SUPABASE_URL and SUPABASE_ANON_KEY:
                # Fallback para anon key
                self.client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                logger.info("Cliente Supabase inicializado com sucesso (anon role)")
            else:
                logger.error("Credenciais Supabase não configuradas")
                raise ValueError("Credenciais Supabase ausentes")
        except Exception as e:
            logger.error(f"Erro ao inicializar Supabase: {e}")
            raise
    
    # === Operações com login_user ===
    
    async def get_user(self, username: str) -> Optional[Dict]:
        """Busca usuário pelo username"""
        try:
            response = self.client.table('login_user').select('*').eq('username', username).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao buscar usuário {username}: {e}")
            return None
    
    async def update_last_login(self, user_id: str):
        """Atualiza último login do usuário"""
        try:
            self.client.table('login_user').update({
                'last_login': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            logger.info(f"Last login atualizado para usuário {user_id}")
        except Exception as e:
            logger.error(f"Erro ao atualizar last login: {e}")
    
    # === Operações com base_conhecimento ===
    
    async def insert_knowledge_base(self, titulo: str, conteudo: str, categoria: str = None, tags: List[str] = None) -> bool:
        """Insere documento na base de conhecimento"""
        try:
            data = {
                'titulo_arquivo': titulo,
                'conteudo': conteudo,
                'categoria': categoria,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.client.table('base_conhecimento').insert(data).execute()
            logger.info(f"Documento '{titulo}' inserido na base de conhecimento")
            return True
        except Exception as e:
            logger.error(f"Erro ao inserir na base de conhecimento: {e}")
            return False
    
    async def search_knowledge_base(self, query: str, limit: int = 10) -> List[Dict]:
        """Busca na base de conhecimento"""
        try:
            # Busca simples por título ou conteúdo
            response = self.client.table('base_conhecimento').select('*').or_(
                f"titulo_arquivo.ilike.%{query}%,conteudo.ilike.%{query}%"
            ).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Erro ao buscar na base de conhecimento: {e}")
            return []
    
    # === Operações com historico_reunioes ===
    
    async def insert_meeting(self, meeting_data: Dict) -> Optional[str]:
        """Insere nova reunião no histórico"""
        try:
            # Preparar dados da reunião
            data = {
                'titulo': meeting_data.get('titulo'),
                'data_reuniao': meeting_data.get('data_reuniao', datetime.now().isoformat()),
                'responsavel': meeting_data.get('responsavel'),
                'area': meeting_data.get('area'),
                'participantes': meeting_data.get('participantes', []),
                'duracao': meeting_data.get('duracao', 0),
                'transcricao_completa': meeting_data.get('transcricao_completa', ''),
                'resumo_executivo': meeting_data.get('resumo_executivo', ''),
                'decisoes': meeting_data.get('decisoes', []),
                'acoes': meeting_data.get('acoes', []),
                'pendencias': meeting_data.get('pendencias', []),
                'insights': meeting_data.get('insights', []),
                'created_at': datetime.now().isoformat()
            }
            
            response = self.client.table('historico_reunioes').insert(data).execute()
            meeting_id = response.data[0]['id'] if response.data else None
            
            logger.info(f"Reunião '{data['titulo']}' inserida com ID: {meeting_id}")
            return meeting_id
        except Exception as e:
            logger.error(f"Erro ao inserir reunião: {e}")
            return None
    
    async def get_meetings(self, limit: int = 50) -> List[Dict]:
        """Lista reuniões do histórico"""
        try:
            response = self.client.table('historico_reunioes').select(
                'id, titulo, data_reuniao, responsavel, area, duracao'
            ).order('data_reuniao', desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Erro ao listar reuniões: {e}")
            return []
    
    async def get_meeting_details(self, meeting_id: str) -> Optional[Dict]:
        """Busca detalhes completos de uma reunião"""
        try:
            response = self.client.table('historico_reunioes').select('*').eq('id', meeting_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes da reunião {meeting_id}: {e}")
            return None
    
    async def search_meetings(self, query: str, limit: int = 20) -> List[Dict]:
        """Busca reuniões por termo"""
        try:
            response = self.client.table('historico_reunioes').select('*').or_(
                f"titulo.ilike.%{query}%,transcricao_completa.ilike.%{query}%,resumo_executivo.ilike.%{query}%"
            ).order('data_reuniao', desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Erro ao buscar reuniões: {e}")
            return []
    
    # === Operações com embeddings (futuro) ===
    
    async def store_embeddings(self, table: str, record_id: str, embeddings: List[float]):
        """Armazena embeddings para busca semântica"""
        # Implementar quando configurar pgvector
        pass
    
    async def semantic_search(self, table: str, query_embedding: List[float], limit: int = 10):
        """Busca semântica usando embeddings"""
        # Implementar quando configurar pgvector
        pass

# Instância singleton do cliente Supabase
supabase_client = SupabaseClient()