#!/usr/bin/env python3
"""
Script de teste para verificar todas as conexões do Sistema AURALIS
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")

def test_environment():
    """Testa configuração do ambiente"""
    print_header("TESTE DE AMBIENTE")
    
    # Verificar arquivo .env
    env_file = Path(".env")
    if env_file.exists():
        print_success("Arquivo .env encontrado")
    else:
        print_error("Arquivo .env não encontrado")
        return False
    
    # Carregar variáveis
    try:
        from shared.config import (SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, 
                                 OPENAI_API_KEY, APP_NAME)
        print_success("Configurações carregadas com sucesso")
        
        # Verificar se as variáveis estão definidas
        configs = {
            "SUPABASE_URL": SUPABASE_URL,
            "SUPABASE_ANON_KEY": SUPABASE_ANON_KEY,
            "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
            "OPENAI_API_KEY": OPENAI_API_KEY
        }
        
        for name, value in configs.items():
            if value:
                # Mostrar apenas parte da chave por segurança
                if "KEY" in name:
                    masked = value[:10] + "..." + value[-10:] if len(value) > 20 else value[:5] + "..."
                    print_success(f"{name}: {masked}")
                else:
                    print_success(f"{name}: {value}")
            else:
                print_error(f"{name}: NÃO DEFINIDA")
        
        return True
        
    except Exception as e:
        print_error(f"Erro ao carregar configurações: {e}")
        return False

def test_supabase_connection():
    """Testa conexão com Supabase"""
    print_header("TESTE DE CONEXÃO SUPABASE")
    
    try:
        from src.database.supabase_client import supabase_client
        
        # Verificar se cliente foi inicializado
        if supabase_client.client:
            print_success("Cliente Supabase inicializado")
        else:
            print_error("Cliente Supabase não inicializado")
            return False
        
        # Teste básico - listar tabelas (não funciona com anon key)
        try:
            # Tentar uma operação simples
            response = supabase_client.client.table('login_user').select('count').execute()
            print_success("Conexão com banco de dados funcionando")
            print_info(f"Teste de contagem executado com sucesso")
            return True
        except Exception as e:
            error_msg = str(e)
            if "Invalid API key" in error_msg:
                print_error("Chave API Supabase inválida")
                print_info("Verifique SUPABASE_ANON_KEY ou SUPABASE_SERVICE_KEY")
            elif "JWT" in error_msg:
                print_error("Problema com autenticação JWT")
                print_info("Verifique SUPABASE_JWT_SECRET")
            else:
                print_error(f"Erro de conexão: {error_msg}")
            return False
            
    except Exception as e:
        print_error(f"Erro ao testar Supabase: {e}")
        return False

def test_openai_connection():
    """Testa conexão com OpenAI"""
    print_header("TESTE DE CONEXÃO OPENAI")
    
    try:
        import openai
        from shared.config import OPENAI_API_KEY, OPENAI_MODEL
        
        if not OPENAI_API_KEY:
            print_error("OPENAI_API_KEY não definida")
            return False
        
        # Configurar cliente
        openai.api_key = OPENAI_API_KEY
        
        # Teste simples
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Usar modelo mais barato para teste
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print_success("Conexão com OpenAI funcionando")
            print_info(f"Modelo testado: gpt-3.5-turbo")
            print_info(f"Modelo configurado: {OPENAI_MODEL}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg.lower():
                print_error("Chave API OpenAI inválida")
                print_info("Verifique OPENAI_API_KEY no arquivo .env")
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                print_error("Problema de cota/cobrança OpenAI")
                print_info("Verifique sua conta OpenAI")
            elif "rate limit" in error_msg.lower():
                print_warning("Limite de taxa atingido")
                print_info("Aguarde alguns minutos e tente novamente")
            else:
                print_error(f"Erro OpenAI: {error_msg}")
            return False
            
    except ImportError:
        print_error("Biblioteca OpenAI não instalada")
        print_info("Execute: pip install openai")
        return False
    except Exception as e:
        print_error(f"Erro ao testar OpenAI: {e}")
        return False

async def test_database_operations():
    """Testa operações do banco de dados"""
    print_header("TESTE DE OPERAÇÕES DO BANCO")
    
    try:
        from src.database.supabase_client import supabase_client
        
        # Teste 1: Buscar usuários
        try:
            user = await supabase_client.get_user("admin")
            if user:
                print_success("Busca de usuário funcionando")
            else:
                print_warning("Usuário 'admin' não encontrado no banco")
        except Exception as e:
            print_error(f"Erro ao buscar usuário: {e}")
        
        # Teste 2: Buscar reuniões
        try:
            meetings = await supabase_client.get_meetings(limit=5)
            print_success(f"Busca de reuniões funcionando ({len(meetings)} encontradas)")
        except Exception as e:
            print_error(f"Erro ao buscar reuniões: {e}")
        
        # Teste 3: Buscar conhecimento
        try:
            docs = await supabase_client.search_knowledge_base("test", limit=1)
            print_success(f"Busca na base de conhecimento funcionando ({len(docs)} documentos)")
        except Exception as e:
            print_error(f"Erro ao buscar conhecimento: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Erro geral em operações do banco: {e}")
        return False

def test_agents():
    """Testa agentes IA"""
    print_header("TESTE DOS AGENTES IA")
    
    try:
        # Teste do orquestrador
        from backend.agents.agente_orquestrador import agente_orquestrador
        print_success("Agente Orquestrador carregado")
        
        # Teste do brainstorm
        from backend.agents.agente_brainstorm import agente_brainstorm
        print_success("Agente Brainstorm carregado")
        
        # Teste da consulta
        from backend.agents.agente_consulta_inteligente import agente_consulta_inteligente
        print_success("Agente Consulta Inteligente carregado")
        
        return True
        
    except Exception as e:
        print_error(f"Erro ao carregar agentes: {e}")
        return False

def test_audio_system():
    """Testa sistema de áudio"""
    print_header("TESTE DO SISTEMA DE ÁUDIO")
    
    try:
        from src.audio.audio_recorder import AudioRecorder
        
        # Criar instância
        recorder = AudioRecorder()
        print_success("AudioRecorder inicializado")
        
        # Listar dispositivos
        devices = recorder.get_available_devices()
        if devices:
            print_success(f"Dispositivos de áudio encontrados: {len(devices)}")
            for i, device in enumerate(devices[:3]):  # Mostrar apenas 3
                print_info(f"  {i+1}. {device['name']}")
        else:
            print_warning("Nenhum dispositivo de áudio encontrado")
            print_info("Normal em ambiente WSL/Docker")
        
        return True
        
    except Exception as e:
        print_error(f"Erro no sistema de áudio: {e}")
        if "pyaudio" in str(e).lower():
            print_info("Execute: sudo apt install portaudio19-dev")
        return False

def generate_diagnosis():
    """Gera diagnóstico com sugestões"""
    print_header("DIAGNÓSTICO E SUGESTÕES")
    
    print_info("Baseado nos testes acima:")
    print()
    
    print("🔧 CREDENCIAIS NECESSÁRIAS:")
    print("   • SUPABASE_URL - URL do projeto Supabase")
    print("   • SUPABASE_ANON_KEY - Chave anônima do Supabase")
    print("   • SUPABASE_SERVICE_KEY - Chave de serviço do Supabase")
    print("   • OPENAI_API_KEY - Chave da API OpenAI")
    print()
    
    print("📝 ONDE OBTER:")
    print("   • Supabase: https://supabase.com/dashboard")
    print("     - Vá em Settings > API")
    print("     - Copie URL, anon key, service_role key")
    print("   • OpenAI: https://platform.openai.com/api-keys")
    print("     - Crie uma nova API key")
    print()
    
    print("🔨 COMANDOS ÚTEIS:")
    print("   • Editar .env: nano .env")
    print("   • Ver logs: tail -f logs/auralis.log")
    print("   • Reinstalar: pip install -r requirements.txt")

async def main():
    """Função principal"""
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║          🎯 AURALIS - Teste de Conexões                  ║
    ║                {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # Executar testes
    results['environment'] = test_environment()
    results['supabase'] = test_supabase_connection()
    results['openai'] = test_openai_connection()
    results['database'] = await test_database_operations()
    results['agents'] = test_agents()
    results['audio'] = test_audio_system()
    
    # Resumo
    print_header("RESUMO DOS TESTES")
    
    for test_name, success in results.items():
        status = "✅ OK" if success else "❌ FALHOU"
        print(f"  {test_name.upper()}: {status}")
    
    # Estatísticas
    total_tests = len(results)
    passed_tests = sum(results.values())
    success_rate = (passed_tests / total_tests) * 100
    
    print()
    print(f"📊 ESTATÍSTICAS:")
    print(f"   • Testes executados: {total_tests}")
    print(f"   • Testes bem-sucedidos: {passed_tests}")
    print(f"   • Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate < 50:
        print_error("Sistema com problemas críticos")
    elif success_rate < 80:
        print_warning("Sistema parcialmente funcional")
    else:
        print_success("Sistema funcionando bem!")
    
    # Diagnóstico
    generate_diagnosis()

if __name__ == "__main__":
    asyncio.run(main())