"""
Backend AURALIS - Sistema integrado com Supabase e OpenAI
Gerencia autenticação, processamento de reuniões e assistente IA
"""

import os
import hashlib
import threading
from datetime import datetime
from typing import Dict, Optional, Callable
from pathlib import Path

from supabase import create_client, Client
from dotenv import load_dotenv

# Importar os novos módulos
try:
    from src.agente_busca_melhorado import AgenteBuscaMelhorado
    AGENTE_MELHORADO = True
except ImportError:
    from src.agente_busca_reunioes import IntegracaoAssistenteReunioes
    AGENTE_MELHORADO = False
from src.embeddings_processor import ProcessadorEmbeddings

load_dotenv()

class AURALISBackend:
    """
    Backend principal do sistema AURALIS
    Integra Supabase para persistência e OpenAI para IA
    """
    
    def __init__(self):
        # Configurar Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Credenciais Supabase não encontradas no .env")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Integração com assistente de reuniões
        if AGENTE_MELHORADO:
            self.assistente_reunioes = AgenteBuscaMelhorado()
        else:
            self.assistente_reunioes = IntegracaoAssistenteReunioes()
        
        # Processador de embeddings
        self.processador_embeddings = ProcessadorEmbeddings()
        
        # Estado do usuário
        self.current_user = None
        
        print("✅ Backend AURALIS inicializado com Supabase")
    
    def hash_password(self, password: str) -> str:
        """Hash de senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Autentica usuário no Supabase
        """
        try:
            # Buscar usuário
            password_hash = self.hash_password(password)
            
            result = self.supabase.table('login_user').select('*').eq(
                'username', username
            ).eq(
                'password_hash', password_hash
            ).eq(
                'is_active', True
            ).execute()
            
            if result.data and len(result.data) > 0:
                self.current_user = result.data[0]
                print(f"✅ Usuário {username} autenticado com sucesso")
                return self.current_user
            else:
                print(f"❌ Falha na autenticação para {username}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            return None
    
    def create_user(self, username: str, password: str, cargo: str = None, area: str = None) -> bool:
        """
        Cria novo usuário no sistema
        """
        try:
            password_hash = self.hash_password(password)
            
            user_data = {
                'username': username,
                'password_hash': password_hash,
                'cargo': cargo,
                'area': area,
                'is_active': True
            }
            
            result = self.supabase.table('login_user').insert(user_data).execute()
            
            if result.data:
                print(f"✅ Usuário {username} criado com sucesso")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erro ao criar usuário: {e}")
            return False
    
    def logout(self):
        """Faz logout do usuário atual"""
        if self.current_user:
            username = self.current_user.get('username', 'Usuário')
            self.current_user = None
            print(f"✅ Usuário {username} deslogado")
    
    def processar_pasta_reunioes(self, caminho_pasta: str):
        """
        Processa pasta com arquivos de reunião
        """
        try:
            self.processador_embeddings.processar_pasta(caminho_pasta)
            return True
        except Exception as e:
            print(f"Erro ao processar pasta: {e}")
            return False
    
    def buscar_informacao_reuniao(self, pergunta: str) -> str:
        """
        Busca informação nas reuniões usando IA
        """
        if AGENTE_MELHORADO:
            return self.assistente_reunioes.processar_pergunta(pergunta)
        else:
            return self.assistente_reunioes.processar_mensagem_usuario(pergunta)

def process_message_async(backend: AURALISBackend, message: str, 
                         callback: Callable[[str], None], 
                         error_callback: Callable[[str], None]):
    """
    Processa mensagem de forma assíncrona
    """
    def _process():
        try:
            # Processar com o assistente de reuniões
            response = backend.buscar_informacao_reuniao(message)
            callback(response)
        except Exception as e:
            error_callback(str(e))
    
    thread = threading.Thread(target=_process)
    thread.daemon = True
    thread.start()

# Função para inicializar usuários padrão
def init_default_users():
    """Cria usuários padrão se não existirem"""
    backend = AURALISBackend()
    
    usuarios_padrao = [
        {
            'username': 'admin',
            'password': 'admin123',
            'cargo': 'Administrador',
            'area': 'TI'
        },
        {
            'username': 'usuario',
            'password': 'senha123',
            'cargo': 'Analista',
            'area': 'Operações'
        }
    ]
    
    for user in usuarios_padrao:
        try:
            # Verificar se usuário já existe
            result = backend.supabase.table('login_user').select('id').eq(
                'username', user['username']
            ).execute()
            
            if not result.data:
                backend.create_user(**user)
                print(f"✅ Usuário padrão '{user['username']}' criado")
            else:
                print(f"ℹ️  Usuário '{user['username']}' já existe")
        except Exception as e:
            print(f"Erro ao criar usuário padrão: {e}")

# Função para processar reuniões de teste
def processar_reunioes_teste():
    """Processa arquivos de teste na pasta teste_reuniao"""
    backend = AURALISBackend()
    pasta_teste = Path(__file__).parent / "teste_reuniao"
    
    if pasta_teste.exists():
        print(f"\n🔄 Processando reuniões em: {pasta_teste}")
        backend.processar_pasta_reunioes(str(pasta_teste))
    else:
        print(f"\n⚠️  Pasta de teste não encontrada: {pasta_teste}")

if __name__ == "__main__":
    print("\n=== INICIALIZAÇÃO DO BACKEND AURALIS ===\n")
    
    # Criar usuários padrão
    print("1. Criando usuários padrão...")
    init_default_users()
    
    # Processar reuniões de teste
    print("\n2. Processando reuniões de teste...")
    processar_reunioes_teste()
    
    # Testar autenticação
    print("\n3. Testando autenticação...")
    backend = AURALISBackend()
    user = backend.authenticate('admin', 'admin123')
    if user:
        print(f"   ✅ Login bem-sucedido: {user['username']} ({user['cargo']})")
        
        # Testar busca
        print("\n4. Testando busca em reuniões...")
        resposta = backend.buscar_informacao_reuniao("Quais foram as principais decisões?")
        print(f"   Resposta: {resposta[:100]}...")
    
    print("\n=== BACKEND PRONTO ===\n")