#!/usr/bin/env python3
"""
Script para criar tabelas do banco de dados AURALIS
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.supabase_client import supabase_client
from shared.config import TEST_USERS
from loguru import logger
import json
from datetime import datetime

def create_tables():
    """Cria tabelas do banco de dados"""
    
    print("🔧 Criando tabelas do banco de dados...")
    
    # SQL para criar tabelas
    sql_commands = [
        # Tabela login_user
        '''
        CREATE TABLE IF NOT EXISTS login_user (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nome_completo TEXT,
            cpf TEXT,
            cargo TEXT,
            area TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE
        );
        ''',
        
        # Tabela base_conhecimento
        '''
        CREATE TABLE IF NOT EXISTS base_conhecimento (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            titulo_arquivo TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            categoria TEXT,
            tags TEXT[],
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        ''',
        
        # Tabela historico_reunioes
        '''
        CREATE TABLE IF NOT EXISTS historico_reunioes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            titulo TEXT NOT NULL,
            data_reuniao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            responsavel TEXT,
            area TEXT,
            participantes TEXT[],
            duracao INTEGER DEFAULT 0,
            transcricao_completa TEXT,
            resumo_executivo TEXT,
            decisoes JSONB DEFAULT '[]'::jsonb,
            acoes JSONB DEFAULT '[]'::jsonb,
            pendencias JSONB DEFAULT '[]'::jsonb,
            insights JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
    ]
    
    try:
        for i, sql in enumerate(sql_commands, 1):
            print(f"  Executando comando {i}/3...")
            result = supabase_client.client.rpc('exec_sql', {'sql': sql.strip()}).execute()
            print(f"  ✅ Comando {i} executado")
            
    except Exception as e:
        print(f"  ❌ Erro ao executar SQL: {e}")
        # Tentar método alternativo
        print("  🔄 Tentando método alternativo...")
        try:
            # Criar tabelas uma por vez usando schema
            tables = [
                ('login_user', sql_commands[0]),
                ('base_conhecimento', sql_commands[1]),
                ('historico_reunioes', sql_commands[2])
            ]
            
            for table_name, sql in tables:
                try:
                    # Verificar se tabela existe
                    result = supabase_client.client.table(table_name).select('count').limit(1).execute()
                    print(f"  ✅ Tabela {table_name} já existe")
                except:
                    print(f"  ⚠️  Tabela {table_name} não existe - precisa ser criada manualmente")
                    print(f"       SQL: {sql[:50]}...")
                    
        except Exception as e2:
            print(f"  ❌ Erro no método alternativo: {e2}")

def insert_test_users():
    """Insere usuários de teste"""
    print("\n👥 Inserindo usuários de teste...")
    
    try:
        for username, user_data in TEST_USERS.items():
            # Verificar se usuário já existe
            existing = supabase_client.client.table('login_user').select('id').eq('username', username).execute()
            
            if existing.data:
                print(f"  ⚠️  Usuário '{username}' já existe")
                continue
            
            # Inserir usuário
            user_record = {
                'username': username,
                'password': user_data['password'],  # Em produção, usar hash
                'nome_completo': user_data['nome_completo'],
                'cargo': user_data['cargo'],
                'area': user_data['area'],
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase_client.client.table('login_user').insert(user_record).execute()
            print(f"  ✅ Usuário '{username}' criado")
            
    except Exception as e:
        print(f"  ❌ Erro ao inserir usuários: {e}")

def insert_sample_data():
    """Insere dados de exemplo"""
    print("\n📝 Inserindo dados de exemplo...")
    
    try:
        # Exemplo de conhecimento
        knowledge_sample = {
            'titulo_arquivo': 'Política de Home Office',
            'conteudo': '''
            Política de Trabalho Remoto

            1. Elegibilidade
            - Funcionários com mais de 6 meses na empresa
            - Aprovação do gestor direto
            - Atividades compatíveis com trabalho remoto

            2. Horários
            - Manter horário comercial padrão
            - Disponibilidade para reuniões
            - Comunicação prévia de ausências

            3. Equipamentos
            - Notebook fornecido pela empresa
            - Acesso VPN obrigatório
            - Responsabilidade pela segurança

            4. Produtividade
            - Metas mantidas ou superadas
            - Relatórios semanais
            - Avaliação trimestral
            ''',
            'categoria': 'politica',
            'tags': ['home office', 'trabalho remoto', 'rh', 'política'],
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase_client.client.table('base_conhecimento').insert(knowledge_sample).execute()
        print("  ✅ Exemplo de conhecimento inserido")
        
        # Exemplo de reunião
        meeting_sample = {
            'titulo': 'Alinhamento de Projeto Alpha',
            'data_reuniao': datetime.now().isoformat(),
            'responsavel': 'João Silva',
            'area': 'Desenvolvimento',
            'participantes': ['João Silva', 'Maria Santos', 'Pedro Costa'],
            'duracao': 45,
            'transcricao_completa': '''
            João: Boa tarde pessoal, vamos começar nossa reunião sobre o Projeto Alpha.
            Maria: Oi João, estou aqui. Podemos começar.
            Pedro: Oi pessoal, pronto para discutir os próximos passos.
            
            João: Primeiro ponto da pauta: revisão do cronograma atual.
            Maria: Estamos no prazo com o desenvolvimento da API.
            Pedro: Frontend está 80% concluído, faltam apenas os testes.
            
            João: Ótimo progresso. Algum bloqueio?
            Maria: Precisamos definir a estrutura do banco para o módulo de relatórios.
            Pedro: Concordo, isso está impactando a finalização da tela de dashboards.
            
            João: Ok, vou agendar uma reunião técnica para amanhã.
            Maria: Perfeito, assim conseguimos desbloquear.
            Pedro: Excelente, obrigado João.
            ''',
            'resumo_executivo': 'Reunião de alinhamento do Projeto Alpha com boa evolução. API no prazo, frontend 80% concluído. Identificado bloqueio na estrutura do banco para relatórios.',
            'decisoes': [
                {
                    'decisao': 'Agendar reunião técnica para definir estrutura do banco',
                    'responsavel': 'João Silva',
                    'prazo': '2025-06-01'
                }
            ],
            'acoes': [
                {
                    'acao': 'Finalizar testes do frontend',
                    'responsavel': 'Pedro Costa',
                    'prazo': '2025-06-03'
                },
                {
                    'acao': 'Preparar proposta de estrutura do banco',
                    'responsavel': 'Maria Santos',
                    'prazo': '2025-06-01'
                }
            ],
            'pendencias': [
                {
                    'pendencia': 'Definição da estrutura do banco para módulo de relatórios'
                }
            ],
            'insights': [
                {
                    'insight': 'Equipe bem alinhada e proativa na identificação de bloqueios'
                }
            ],
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase_client.client.table('historico_reunioes').insert(meeting_sample).execute()
        print("  ✅ Exemplo de reunião inserido")
        
    except Exception as e:
        print(f"  ❌ Erro ao inserir dados de exemplo: {e}")

def main():
    """Função principal"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           🎯 AURALIS - Configuração do Banco           ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Verificar conexão
    if not supabase_client.client:
        print("❌ Erro: Cliente Supabase não inicializado")
        return
    
    print("✅ Conexão com Supabase OK")
    
    # Criar tabelas
    create_tables()
    
    # Inserir usuários de teste
    insert_test_users()
    
    # Inserir dados de exemplo
    insert_sample_data()
    
    print("\n🎉 Configuração do banco concluída!")
    print("\n📋 Próximos passos:")
    print("   1. Execute: python main.py")
    print("   2. Faça login com: admin / admin123")
    print("   3. Teste todas as funcionalidades")

if __name__ == "__main__":
    main()