"""
Gerenciador de autenticação do sistema AURALIS
Baseado no auth_manager do projeto windows/
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime
from supabase import create_client, Client
from loguru import logger
import sys
sys.path.append('..')
from shared.config import SUPABASE_URL, SUPABASE_ANON_KEY, TEST_USERS

class AuthManager:
    """Gerencia autenticação e sessão do usuário"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.current_user: Optional[Dict] = None
        self.initialize_supabase()
    
    def initialize_supabase(self):
        """Inicializa cliente Supabase"""
        try:
            if SUPABASE_URL and SUPABASE_ANON_KEY:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                logger.info("Cliente Supabase inicializado com sucesso")
            else:
                logger.warning("Credenciais Supabase não configuradas, usando modo offline")
        except Exception as e:
            logger.error(f"Erro ao inicializar Supabase: {e}")
            self.supabase = None
    
    async def login(self, username: str, password: str) -> Dict:
        """
        Realiza login do usuário
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            Dict com resultado do login
        """
        try:
            # Tentar autenticação real com Supabase
            if self.supabase:
                try:
                    # Buscar usuário no banco
                    response = self.supabase.table('login_user').select('*').eq('username', username).single().execute()
                    
                    if response.data:
                        user_data = response.data
                        # Aqui você faria a verificação real da senha (hash)
                        # Por enquanto, comparação simples para desenvolvimento
                        if user_data.get('password') == password:
                            self.current_user = {
                                'id': user_data.get('id'),
                                'username': user_data.get('username'),
                                'nome_completo': user_data.get('nome_completo'),
                                'cargo': user_data.get('cargo'),
                                'area': user_data.get('area')
                            }
                            
                            # Atualizar last_login
                            self.supabase.table('login_user').update({
                                'last_login': datetime.now().isoformat()
                            }).eq('id', user_data.get('id')).execute()
                            
                            logger.info(f"Login bem-sucedido para usuário: {username}")
                            return {
                                "success": True,
                                "user": self.current_user,
                                "message": "Login realizado com sucesso!"
                            }
                except Exception as e:
                    logger.warning(f"Erro na autenticação Supabase: {e}")
            
            # Fallback para usuários de teste
            if username in TEST_USERS and TEST_USERS[username]['password'] == password:
                self.current_user = {
                    'username': username,
                    'nome_completo': TEST_USERS[username]['nome_completo'],
                    'cargo': TEST_USERS[username]['cargo'],
                    'area': TEST_USERS[username]['area']
                }
                logger.info(f"Login bem-sucedido (modo teste) para usuário: {username}")
                return {
                    "success": True,
                    "user": self.current_user,
                    "message": "Login realizado com sucesso!"
                }
            
            logger.warning(f"Tentativa de login falhou para usuário: {username}")
            return {
                "success": False,
                "message": "Usuário ou senha incorretos"
            }
            
        except Exception as e:
            logger.error(f"Erro durante login: {e}")
            return {
                "success": False,
                "message": f"Erro ao processar login: {str(e)}"
            }
    
    def logout(self):
        """Realiza logout do usuário"""
        username = self.current_user.get('username') if self.current_user else 'desconhecido'
        self.current_user = None
        logger.info(f"Logout realizado para usuário: {username}")
    
    def is_authenticated(self) -> bool:
        """Verifica se há usuário autenticado"""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """Retorna dados do usuário atual"""
        return self.current_user

# Instância singleton do gerenciador de autenticação
auth_manager = AuthManager()